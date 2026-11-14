import pymupdf
import chromadb
import uuid #unique identifier for each uploaded PDF session.

from chromadb.errors import NotFoundError

from pydantic import BaseModel, Field #what information the API expects.

from contextlib import asynccontextmanager
from sentence_transformers import SentenceTransformer

from fastapi import FastAPI, File, HTTPException, UploadFile, Request

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Loading embedding model...")

    app.state.embedding_model = SentenceTransformer(
        "sentence-transformers/all-MiniLM-L6-v2",
        device="cpu"
    )
    app.state.chroma_client = chromadb.EphemeralClient()

    print("ChromaDB in-memory client initialized.")

    print("Embedding model loaded successfully.")

    yield

    # Application shutdown
    app.state.embedding_model = None
    app.state.chroma_client = None

    print("Embedding model resources released.")
    print("ChromaDB client reference released.")

app = FastAPI(
    title="AI Document Assistant",
    description="AI-powered PDF question-answering application",
    version="0.1.0",
    lifespan=lifespan
)

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

class SearchRequest(BaseModel):
    session_id: str = Field(pattern=r"^[0-9a-f]{32}$")
    query: str = Field(min_length=1, max_length=1000)
    top_k: int = Field(default=5, ge=1, le=10)

def create_text_chunks(pages, chunk_size=200, overlap=40):
    chunks = []

    for page in pages:
        words = page["text"].split()
        start = 0
        chunk_index = 1

        while start < len(words):
            end = min(start + chunk_size, len(words))

            chunk_text = " ".join(words[start:end])

            chunks.append({
                "chunk_id": len(chunks) + 1,
                "page_number": page["page_number"],
                "chunk_index": chunk_index,
                "text": chunk_text
            })

            if end == len(words):
                break

            start = end - overlap
            chunk_index += 1

    return chunks

@app.get("/")
def root():
    return {
        "message": "Welcome to AI Document Assistant",
        "status": "running"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "application": "AI Document Assistant"
    }

@app.post("/documents/upload")
async def upload_document(
    request: Request,
    file: UploadFile = File(...)
):

    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed"
        )

    content = await file.read(MAX_FILE_SIZE + 1)
    await file.close()

    if not content:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty"
        )

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="File size exceeds the 10 MB limit"
        )

    # Open the PDF directly from memory
    try:
        document = pymupdf.open(
            stream=content,
            filetype="pdf"
        )
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Invalid or unreadable PDF file"
        )

    if document.needs_pass:
        document.close()
        raise HTTPException(
            status_code=400,
            detail="Password-protected PDFs are not supported"
        )

    pages = []

    try:
        for page_number, page in enumerate(document, start=1):
            extracted_text = page.get_text("text").strip()

            pages.append({
                "page_number": page_number,
                "text": extracted_text
            })
    finally:
        document.close()

    total_characters = sum(
        len(page["text"]) for page in pages
    )

    chunks = create_text_chunks(pages)

    embedding_model = request.app.state.embedding_model

    if chunks:
        texts = [chunk["text"] for chunk in chunks]

        embeddings = embedding_model.encode(
            texts,
            convert_to_numpy=True,
            show_progress_bar=False
        )

        embedding_dimensions = int(embeddings.shape[1])
        embedding_preview = embeddings[0][:5].tolist()

    else:
        embedding_dimensions = 0
        embedding_preview = []

    # Initialize document session details
    session_id = None
    stored_vectors = 0
    collection_name = None

    if chunks:
        session_id = uuid.uuid4().hex
        collection_name = f"document_{session_id}"

        collection = request.app.state.chroma_client.create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )

        collection.add(
            ids=[
                f"chunk_{chunk['chunk_id']}"
                for chunk in chunks
            ],
            documents=texts,
            embeddings=embeddings.tolist(),
            metadatas=[
                {
                    "page_number": chunk["page_number"],
                    "chunk_index": chunk["chunk_index"],
                    "filename": file.filename,
                    "session_id": session_id
                }
                for chunk in chunks
            ]
        )

        stored_vectors = collection.count()

    return {
        "message": "PDF processed successfully",
        "filename": file.filename,
        "page_count": len(pages),
        "total_characters": total_characters,
        "has_extractable_text": total_characters > 0,
        "chunk_count": len(chunks),
        "session_id": session_id,
        "collection_name": collection_name,
        "stored_vectors": stored_vectors,
        "embeddings_generated": len(chunks),
        "embedding_dimensions": embedding_dimensions,
        "embedding_preview": embedding_preview,
        "chunks": chunks
    }


@app.post("/documents/search")
def search_document(
    payload: SearchRequest,
    request: Request
):
    # Step 1: Identify the document collection
    collection_name = f"document_{payload.session_id}"

    try:
        collection = request.app.state.chroma_client.get_collection(
            name=collection_name
        )
    except NotFoundError:
        raise HTTPException(
            status_code=404,
            detail="Document session not found or expired"
        ) from None

    # Step 2: Generate embedding for the user's question
    embedding_model = request.app.state.embedding_model

    query_embedding = embedding_model.encode(
        [payload.query],
        convert_to_numpy=True,
        show_progress_bar=False
    )[0].tolist()

    # Step 3: Determine the number of results
    result_limit = min(payload.top_k, collection.count())

    # Step 4: Search for similar vectors
    search_results = collection.query(
        query_embeddings=[query_embedding],
        n_results=result_limit,
        include=["documents", "metadatas", "distances"]
    )

    # Step 5: Format matching results
    matches = []

    for chunk_id, document, metadata, distance in zip(
        search_results["ids"][0],
        search_results["documents"][0],
        search_results["metadatas"][0],
        search_results["distances"][0]
    ):
        matches.append({
            "chunk_id": chunk_id,
            "text": document,
            "page_number": metadata["page_number"],
            "chunk_index": metadata["chunk_index"],
            "distance": round(float(distance), 4)
        })

    return {
        "session_id": payload.session_id,
        "query": payload.query,
        "results_count": len(matches),
        "results": matches
    }

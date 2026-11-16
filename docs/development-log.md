# AI Document Assistant — Development Log

## Project objective

Build an API-based application that accepts a PDF, extracts its text, divides the text into manageable chunks, and eventually supports semantic retrieval and question answering.

**Current processing decision:** uploaded PDFs are processed in memory. The current upload endpoint does not save the original PDF to permanent disk storage or a database. The `storage/uploads/` directory was created during setup but is not used by the current endpoint.

## Development environment

| Item | Current setup |
|---|---|
| Operating system | Ubuntu 26.04.1 LTS |
| Language | Python 3.14.4 |
| Virtual environment | `.venv` in the project root |
| API framework | FastAPI |
| ASGI server | Uvicorn |
| API documentation | OpenAPI, exposed through Swagger UI |
| PDF processing | PyMuPDF 2.1 |
| Multipart upload support | `python-multipart` |
| Local development URL | `http://127.0.0.1:8000` |

The virtual environment directory persists after a terminal is closed. It must be activated separately in each new terminal:

```bash
source .venv/bin/activate
```

Start the development server from the project root:

```bash
uvicorn app.main:app --reload
```

Keep the server terminal open. Use a second terminal for `curl`, package management, Git, and other commands. `Ctrl+C` stops the server; `Ctrl+Z` suspends it, and `fg` resumes a suspended foreground job.

## API routes implemented

| Method | Path | Purpose | Status |
|---|---|---|---|
| GET | `/` | Returns a welcome message and running status | Implemented and tested |
| GET | `/health` | Returns application health status | Implemented and tested |
| POST | `/documents/upload` | Validates an uploaded PDF, extracts page text, and returns text chunks | Implemented and tested |

FastAPI generates the OpenAPI schema from registered route definitions. The schema is available at `/openapi.json`; Swagger UI is available at `/docs`.

## PDF processing implementation

The upload endpoint currently performs these steps:

1. Checks that the supplied filename ends in `.pdf`.
2. Reads at most 10 MB plus one byte so the endpoint can detect an oversized upload.
3. Rejects an empty upload and files exceeding the 10 MB limit.
4. Opens the PDF directly from the uploaded bytes using `pymupdf.open(stream=content, filetype="pdf")`.
5. Rejects unreadable or invalid PDFs and password-protected PDFs.
6. Extracts text from each page using `page.get_text("text")`.
7. Closes the PyMuPDF document.
8. Splits each page's extracted text into chunks and returns the results as JSON.

The PDF bytes are not written to `storage/uploads/`, nor are they persisted in a database. The endpoint returns extracted text in the response. The current implementation is intended for development and testing; production hardening is still required.

## Text chunking

The `create_text_chunks(pages, chunk_size=200, overlap=40)` helper:

- Splits each page's text into words.
- Creates chunks of up to 200 words.
- Uses a 40-word overlap between consecutive chunks from the same page.
- Adds `chunk_id`, `page_number`, `chunk_index`, and `text` to each chunk.
- Does not combine text across page boundaries.

### Verified test result

A 30-page text-based PDF (`file-example_PDF_1MB.pdf`) was uploaded through Swagger.

| Metric | Observed result |
|---|---:|
| HTTP status | 200 |
| Page count | 30 |
| Extracted characters | 50,148 |
| Extractable text | `true` |
| Generated chunks | 54 |

A small sample PDF also returned extracted text successfully (`Dummy PDF file`). These tests confirm text extraction and chunk generation for text-based PDFs. They do **not** demonstrate OCR for image-only scanned PDFs.

## Troubleshooting notes

### A file named `.pdf` was rejected

A resume file had a `.pdf` filename, but the Linux `file` command identified its contents as `Microsoft Word 2007+`. The file was a Word document (DOCX) with a PDF extension. The actual file content, not merely its filename, determines whether a PDF parser can read it.

Useful check:

```bash
file ~/Downloads/your-document.pdf
```

### Swagger appeared not to load

The Uvicorn process had been suspended with `Ctrl+Z`. `fg` resumed the process. The `/docs` and `/openapi.json` routes both returned HTTP 200 when the server was running.

### Inspect listening TCP ports

```bash
ss -ltnp
```

During the lab, FastAPI/Uvicorn was listening on `127.0.0.1:8000`. The existing monitoring lab also showed listeners on ports 9090 (Prometheus) and 3000 (Grafana). The FastAPI binding to `127.0.0.1` means it is reachable locally on that machine, not directly from another computer using the machine's LAN address.

## Current limitations

- OCR is not implemented. Image-only scanned pages may produce empty extracted text.
- The endpoint returns the chunk text in the HTTP response; large-document responses can become large. A later API design should return a smaller summary or processing result instead of all chunk contents.
- Chunks are not yet converted into embeddings.
- Chunks are not yet indexed in ChromaDB or another vector database.
- Question answering and LLM integration are not implemented.
- Authentication, rate limiting, deeper PDF validation, structured error handling, and production deployment hardening remain future work.

## Next planned work

1. Generate an embedding vector for every text chunk.
2. Add a vector index (planned: ChromaDB) for similarity search.
3. Embed a user question and retrieve relevant chunks.
4. Add question answering using retrieved context and an LLM.
5. Evaluate OCR for scanned PDFs as a separate enhancement.

Do not describe embeddings, vector search, OCR, permanent storage, or LLM question answering as completed until they have been implemented and tested.

---

## Latest milestone — Embeddings and in-memory vector storage

**Milestone date:** 13 November 2026

### 1. Sentence Transformers installation

Installed Sentence Transformers inside the project's `.venv`.

| Package | Observed version |
|---|---:|
| sentence-transformers | 6.3.0 |
| torch | 2.15.0 |
| transformers | 5.22.2 |
| chromadb | 1.5.9 |

The model used:

`sentence-transformers/all-MiniLM-L6-v2`

Model execution was verified on CPU. PyTorch reported CUDA unavailable and GPU count 0.

### 2. Model lifecycle management

Integrated model initialization into FastAPI's lifespan function.

- The embedding model is loaded during application startup.
- The model is made available through `app.state.embedding_model`.
- Upload requests reuse the loaded model.
- The application clears its model reference during shutdown.

The model is loaded once per application process, not once per PDF upload. Multiple application worker processes would each have their own model instance.

### 3. Embedding generation

Connected Sentence Transformers to the existing PDF processing pipeline.

For every extracted text chunk:

- The chunk text is passed to the embedding model.
- The model generates a numerical vector.
- The selected model produces 384-dimensional embeddings.
- Embeddings are temporarily held in memory.

The test PDF produced 54 chunks and 54 embeddings.

### 4. ChromaDB installation and initialization

Installed ChromaDB 1.5.9 in the project virtual environment.

Used:

`chromadb.EphemeralClient()`

The client is initialized during FastAPI startup and stored in:

`app.state.chroma_client`

This provides temporary in-memory vector storage rather than persistent disk storage.

### 5. Document collection and vector insertion

For each uploaded document containing extractable text:

1. Generate a unique session identifier using Python's `uuid` module.
2. Create a collection named using the `document_` prefix and unique identifier.
3. Configure cosine similarity using `metadata={"hnsw:space": "cosine"}`.
4. Insert chunk IDs and text documents.
5. Insert the corresponding 384-dimensional embedding vectors.
6. Store metadata including page number, chunk index, filename and session ID.
7. Count the stored vectors using `collection.count()`.

The upload response includes the session ID, collection name, chunk count, embedding information and stored-vector count.

### 6. Verified end-to-end test

Uploaded `file-example_PDF_1MB.pdf` through Swagger after integrating ChromaDB.

| Metric | Verified result |
|---|---:|
| HTTP status | 200 |
| PDF pages | 30 |
| Extracted characters | 50,148 |
| Generated chunks | 54 |
| Generated embeddings | 54 |
| Embedding dimensions | 384 |
| Vectors stored in ChromaDB | 54 |

The API returned a unique session ID and collection name.

This confirms successful PDF extraction, chunking, embedding generation and vector insertion for this test document.

### 7. Storage and lifecycle behaviour

The current design uses ChromaDB's ephemeral in-memory client.

- Original PDF files are not permanently saved.
- Vectors and associated chunk data are kept in the in-memory collection.
- Data is lost when the application process terminates or restarts.
- Browser refresh or browser closure alone does not delete the in-memory collection.
- Explicit session expiry and collection cleanup have not yet been implemented.
- Authentication and ownership checks for document sessions have not yet been implemented.

The current implementation is suitable for development and testing, not yet a production-ready multi-user document service.

#### 8. Semantic Search Implementation

**Implementation date:** 16 November 2026

Implemented the semantic search API using FastAPI, Sentence Transformers and ChromaDB.

#### 8.1 Search request validation

Created a Pydantic `SearchRequest` model with:

- `session_id`: Validates a 32-character lowercase hexadecimal session identifier.
- `query`: Accepts a question between 1 and 1,000 characters.
- `top_k`: Controls the maximum number of retrieved chunks (1–10), defaulting to 5.

#### 8.2 Search API endpoint

Implemented:

`POST /documents/search`

The endpoint performs the following operations:

1. Receives the session ID, search query and top-k value.
2. Constructs the corresponding ChromaDB collection name.
3. Retrieves the document collection using `get_collection()`.
4. Handles missing collections with HTTP 404.
5. Generates an embedding for the user's question using the existing Sentence Transformer model.
6. Performs vector similarity search using ChromaDB's `collection.query()`.
7. Retrieves document text, metadata and cosine distances.
8. Returns matching chunks with page numbers and chunk indexes.

#### 8.3 Search API testing

Tested the endpoint through FastAPI Swagger UI.

| Test | Result |
|---|---|
| API endpoint registration | Passed |
| Valid session ID | Passed |
| Invalid/nonexistent session ID | HTTP 404 |
| Valid search request | HTTP 200 |
| Top-k retrieval | 5 results returned |
| Document metadata retrieval | Returned |
| Similarity distance retrieval | Returned |

The PDF upload and semantic search workflows were tested using a 30-page sample PDF containing 54 chunks and 54 stored vectors.

The search endpoint successfully retrieved five matching chunks for the test query `Lorem ipsum dolor sit amet`.

Retrieval relevance and ranking quality still require further evaluation with a broader set of questions.

#### 8.4 Important implementation details

- Each successful PDF upload creates a separate ChromaDB collection.
- The session ID identifies the collection associated with that upload.
- Multiple uploaded documents remain searchable while the same application process is running.
- The application uses `chromadb.EphemeralClient()`.
- Collections are lost when the application process terminates or restarts.
- The search API reuses the embedding model loaded during application startup.

#### 8.5 Git milestone

Implemented and pushed the semantic search API to the GitHub repository.

Commit message:

`Implement semantic document search API`

### 9. Current Project Status

**Completed and verified:**

- FastAPI application and lifecycle management.
- PDF upload and validation.
- PDF text extraction using PyMuPDF.
- Page-based text chunking with overlap.
- Sentence Transformer model integration.
- CPU-based embedding generation.
- ChromaDB in-memory vector storage.
- Unique collection creation for each document upload.
- Pydantic search request validation.
- Semantic search API implementation.
- ChromaDB vector similarity retrieval.
- Search response with document text, page numbers and distances.
- Git commit and push of semantic search implementation.

### 10. Pending Implementation

1. Session expiration and automatic ChromaDB collection cleanup.
2. Persistent vector storage so document collections survive application restarts.
3. Authentication, document ownership and session isolation.
4. LLM integration for grounded question answering (RAG).
5. OCR support for image-only scanned PDFs.
6. Automated unit and API integration testing.
7. Application monitoring and observability using Prometheus and Grafana.
8. Security hardening and performance optimization.
9. Dockerization and deployment.
10. Final documentation and production-readiness review.

### 11. Next Development Milestone

**LLM-powered question answering using Retrieval-Augmented Generation (RAG).**

The next milestone is to integrate an LLM with the existing semantic search functionality.

The application will:

1. Accept a user's question and document session ID.
2. Retrieve relevant document chunks from ChromaDB.
3. Construct a context-aware prompt using the retrieved chunks.
4. Send the prompt and context to an LLM.
5. Generate an answer grounded in the uploaded document.
6. Return the answer with relevant page references.

The existing PDF upload, text extraction, chunking, embedding generation, vector storage and semantic retrieval components will be reused.
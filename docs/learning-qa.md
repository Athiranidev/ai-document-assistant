# AI Document Assistant — Learning Q&A

This note records the questions raised during development, the concepts behind them, and interview-ready explanations. The answers describe the current project; planned features are labelled as planned.

## 1. What is FastAPI, and how are endpoints registered?

**Answer:** FastAPI is the Python web framework used to define the application's HTTP API. I create an application instance with `app = FastAPI(...)` and register routes using decorators such as `@app.get("/health")` and `@app.post("/documents/upload")`. When the application starts, FastAPI loads the route definitions and generates an OpenAPI specification from them.

## 2. How does Swagger know which endpoints exist?

**Answer:** FastAPI generates an OpenAPI schema from the registered routes. The schema is available at `/openapi.json`, and Swagger UI reads that schema and displays the API documentation at `/docs`. I do not manually copy endpoint definitions into Swagger.

## 3. Does Swagger capture commands or responses that I ran in the terminal or Postman?

**Answer:** No. Postman, `curl`, and Swagger UI are separate API clients. They can send requests to the same backend, but one client's response history is not automatically copied into another. Swagger discovers the API structure from OpenAPI; when I click Execute in Swagger, it sends a new HTTP request and displays that request's response.

## 4. What is the difference between the base URL and an endpoint path?

**Answer:** The base URL identifies the server, and the path identifies the resource or operation. For example, `http://127.0.0.1:8000` is the local base URL, while `/health` is an endpoint path. Together they form `http://127.0.0.1:8000/health`.

- `127.0.0.1` means the computer making the request (localhost).
- `8000` is the server's listening port in this project.
- `/docs`, `/openapi.json`, and `/health` are different paths on the same application.

If another developer uses `127.0.0.1` on their own computer, it points to their own computer, not mine. To share a local development server on a network, it must listen on an appropriate network interface and firewall/network access must permit the connection. A deployed application can instead be reached through its configured public hostname or domain.

## 5. Why can two developers open the same Swagger URL?

**Answer:** If both access the same deployed host and path, they receive Swagger UI for the same deployed application's OpenAPI schema. For example, `https://api.example.com/docs` and `https://api.example.com/openapi.json` refer to the documentation UI and schema on that host. The `/docs` path is an application route, not necessarily a physical folder.

## 6. What is Uvicorn, and what does `uvicorn app.main:app --reload` mean?

**Answer:** Uvicorn is the ASGI server that runs the FastAPI application.

- `uvicorn` starts the server.
- `app.main` tells Uvicorn to import the `main` module from the `app` package (`app/main.py`).
- `:app` selects the FastAPI instance named `app` in that module.
- `--reload` watches source files and restarts the development server when code changes. It is intended for development, not production deployment.

## 7. Why use a Python virtual environment?

**Answer:** A virtual environment isolates the project's Python packages from the system Python and from other projects. The `.venv` directory remains on disk after a terminal closes, but activation is per terminal session:

```bash
source .venv/bin/activate
```

I do not need to recreate the environment each time I open a terminal.

## 8. How can I run commands while Uvicorn is running?

**Answer:** I keep Uvicorn running in one terminal and open a second terminal for commands such as `curl`, package installation, and Git. I activate the same project virtual environment in the second terminal. `Ctrl+C` stops Uvicorn. `Ctrl+Z` suspends the process; `fg` resumes a suspended job in that shell.

## 9. How do I identify which port an application is listening on?

**Answer:** I use `ss -ltnp` to list listening TCP sockets and, where permissions allow, their owning processes. In this project, Uvicorn was listening on `127.0.0.1:8000`. The same check showed the existing Prometheus and Grafana listeners on ports 9090 and 3000.

## 10. What is the difference between a server port and a client port?

**Answer:** In a request to `127.0.0.1:8000`, port 8000 is the server's destination/listening port. The client normally uses a temporary source port for its connection. Uvicorn access logs can show the client address and source port, the requested method and path, and the HTTP status. An IP address identifies a network endpoint, not necessarily the individual person using it.

## 11. Does HTTP 200 mean that an uploaded file has been saved permanently?

**Answer:** No. HTTP 200 indicates that the request was handled successfully according to the endpoint's logic. Permanent storage happens only if the application explicitly writes the file to disk, object storage, or a database. Our current endpoint processes the PDF in memory and does not persist the original file.

## 12. Why was a file with a `.pdf` extension rejected?

**Answer:** A filename extension is not proof of the file's real format. The Linux `file` command identified one file named with a `.pdf` extension as `Microsoft Word 2007+`, which indicates DOCX content. PyMuPDF could not open it as a PDF. I should verify that the document was actually exported to PDF and select the exported PDF file.

## 13. How does the current PDF upload endpoint work?

**Answer:** The endpoint receives a multipart file upload, checks the filename extension and size, reads the bytes into memory, and opens the bytes with PyMuPDF. It extracts text from each page, closes the PDF document, and sends the extracted content through the JSON response. It does not save the original PDF to permanent storage.

## 14. Why can a scanned PDF return empty text?

**Answer:** A text-based PDF contains a text layer that a PDF library can extract. A scanned PDF may contain only page images, with no embedded text. `page.get_text("text")` cannot recognize words in an image by itself. OCR (Optical Character Recognition) is needed for image-only pages. OCR has not yet been implemented in this project.

## 15. What is text chunking, and why do we use overlap?

**Answer:** Chunking divides long extracted text into smaller sections. The current helper creates chunks of up to 200 words with a 40-word overlap between consecutive chunks on the same page. The overlap helps retain context that might otherwise be split at a chunk boundary. Each chunk records its `chunk_id`, `page_number`, `chunk_index`, and text. The current implementation chunks each page separately and does not combine text across page boundaries.

## 16. What did the 30-page PDF test prove?

**Answer:** The test returned HTTP 200, detected 30 pages, extracted 50,148 characters, reported extractable text, and generated 54 chunks. This verifies text extraction and chunk generation for that text-based sample. It does not prove OCR works or that embeddings and question answering have been implemented.

## 17. What are embeddings and a vector database? (Next planned stage)

**Answer:** An embedding model converts text into a numerical vector that represents aspects of its meaning. A vector database/index can compare those vectors and retrieve chunks that are semantically similar to a query. These features are planned next; they are not implemented yet in this project.

## Interview explanation of the work completed so far

> I built a Python REST API using FastAPI and ran it with Uvicorn inside a project-specific virtual environment. I registered root, health-check, and PDF-upload endpoints. FastAPI generated the OpenAPI specification, which I inspected through Swagger UI. I tested the APIs using Swagger and `curl`. For the document endpoint, I used PyMuPDF to process uploaded PDF bytes in memory, extract text page by page, and divide the text into chunks with page references and overlap. I tested this with a 30-page text-based PDF and verified that it produced 54 chunks. The current implementation does not persist the uploaded PDF, perform OCR, generate embeddings, or answer questions yet.

## Questions to revisit during the next stages

- How do we choose an embedding model and determine its vector dimension?
- Why must the question and document chunks use the same embedding model?
- How does vector similarity search retrieve relevant chunks?
- How will the application retain chunk metadata while keeping the original PDF temporary?
- How will the API handle scanned PDFs and OCR output?
- How do we avoid returning very large chunk payloads to API clients?

---

# Latest learning session — Embeddings and ChromaDB
Date: 13 November 2026

## 18. What is an embedding model?

Answer: An embedding model is a trained neural network that converts text into a numerical vector representing aspects of its meaning. We use sentence-transformers/all-MiniLM-L6-v2. It produces 384-dimensional vectors.

## 19. What does an embedding model contain?

Answer: A trained model consists of a neural-network architecture, learned numerical weights, and configuration/tokenizer components. The learned weights are reused to process different text inputs. We do not train a new model for every uploaded document.

## 20. Can one model process documents from multiple users?

Answer: Yes. The same loaded model can process different users' documents. It receives different text inputs and generates different embedding vectors. Its learned weights do not change during normal inference. Each application worker process generally has its own model instance.

## 21. Why do we load the embedding model during FastAPI startup?

Answer: Loading a model is relatively expensive in time and memory. We use FastAPI lifespan management to load the model once when the application starts and reuse it across requests. This avoids repeatedly initializing the model for every PDF upload.

## 22. What are application startup, lifespan and shutdown?

Answer:
- Startup: Initialize resources such as the Sentence Transformer model and ChromaDB client.
- Running: Handle API requests using those initialized resources.
- Shutdown: Release application references and allow resources to be cleaned up.

We use Python's asynccontextmanager and FastAPI's lifespan parameter for this lifecycle.

## 23. Why do we use a CPU or GPU for embeddings?

Answer: Both CPUs and GPUs can execute model inference. A CPU is a general-purpose processor and is sufficient for our current small prototype. A GPU can accelerate suitable parallel mathematical operations, especially for larger workloads and batches. Our PyTorch test reported CUDA unavailable and zero CUDA devices, so we explicitly selected CPU execution.

## 24. What does 384-dimensional embedding mean?

Answer: The selected all-MiniLM-L6-v2 model produces a vector containing 384 numerical values for each input text. If we have 54 chunks, their embedding matrix has a shape of 54 by 384.

## 25. Why do we generate embeddings after text chunking?

Answer: Chunking divides a document into manageable text sections. Sentence Transformers converts each section into a numerical vector. These vectors allow us to search for semantically relevant passages instead of relying only on exact keyword matches.

## 26. What is ChromaDB?

Answer: ChromaDB is a vector database that can store embeddings along with their associated text and metadata, and retrieve similar vectors. We use it to store document chunks and their embeddings for later semantic search.

## 27. What is ChromaDB EphemeralClient?

Answer: EphemeralClient creates an in-memory ChromaDB client. Its data is temporary and is not persisted to disk. In our application, the client is initialized during FastAPI startup and stored in app.state.chroma_client. Its data is lost when the application process terminates or restarts.

## 28. Does closing or refreshing the browser delete the ChromaDB data?

Answer: No. Browser refresh or closure does not automatically delete server-side in-memory collections. The collections remain in the application process until explicitly deleted or the process terminates. We still need to implement session expiration and automatic cleanup.

## 29. How do we separate uploaded documents in ChromaDB?

Answer: Our current upload implementation generates a unique UUID-based session ID and creates a collection name using the document_ prefix. Each upload gets its own collection. We also store the session ID, filename, page number and chunk index as metadata. Authentication, ownership checks and secure multi-user access controls are not yet implemented.

## 30. What exactly happens when a PDF is uploaded now?

Answer:
1. FastAPI receives and validates the PDF.
2. PyMuPDF extracts text page by page from the uploaded bytes in memory.
3. Python divides the extracted text into chunks.
4. Sentence Transformers generates a 384-dimensional embedding for each chunk.
5. The application creates a unique ChromaDB collection.
6. ChromaDB stores the chunk IDs, text, embeddings and metadata in memory.
7. The API returns the processing result, session ID and stored-vector count.

## 31. What did our ChromaDB integration test prove?

Answer: We uploaded a 30-page text-based PDF and verified:

- 30 pages detected.
- 50,148 characters extracted.
- 54 text chunks generated.
- 54 embeddings generated.
- 384 dimensions per embedding.
- 54 vectors inserted into ChromaDB.
- HTTP 200 response.

We subsequently implemented and tested semantic search using the stored vectors. The search endpoint successfully returned five matching chunks for a test query.

## 32. What is the difference between model, document and embedding?

Answer:
- Model: The trained mathematical engine that processes text.
- Document: The user's uploaded input.
- Embedding: The numerical vector generated from the document's text.

One loaded model can process many different documents and generate different embeddings.

## 33. What happens to the model and ChromaDB when FastAPI stops?

Answer: The application shutdown handler clears the references to the embedding model and ChromaDB client. When the process terminates, the in-memory ChromaDB data is lost. The downloaded pretrained model files remain in the local Hugging Face cache and do not need to be downloaded again on every startup.

### 34. What is the difference between embedding generation and semantic search?

Answer:

- Embedding generation converts text into a numerical vector.
- Semantic search converts a user's question into an embedding and compares it with stored document embeddings.
- ChromaDB retrieves the most relevant document chunks based on vector similarity.

Our application now supports both document embedding generation and semantic search through the `/documents/search` endpoint.

## 35. What is Pydantic, and why did we use it?

Answer: Pydantic is a Python data validation library. FastAPI uses Pydantic models to validate incoming API request data.

We created a SearchRequest model using BaseModel and Field to validate the session ID, query and top_k values.

## 36. What is the purpose of the session_id?

Answer: The session ID uniquely identifies an uploaded document session.

We generate it using:

uuid.uuid4().hex

The ID is used to construct the corresponding ChromaDB collection name.

## 37. Why does each uploaded PDF get a different ChromaDB collection?

Answer: Each successful PDF upload generates a new UUID and creates a separate collection.

For example:

- PDF A → document_<session_A>
- PDF B → document_<session_B>

This allows the application to search the collection associated with a particular uploaded document.

## 38. How does the semantic search endpoint find the correct collection?

Answer: It receives the session ID from the user's request and constructs the collection name:

collection_name = f"document_{payload.session_id}"

It then retrieves the collection using ChromaDB's get_collection() method.

## 39. Why do we generate an embedding for the user's question?

Answer: ChromaDB stores the document chunks as numerical vectors. To perform semantic search, the user's question must also be converted into a vector using the same embedding model.

Our application reuses the Sentence Transformer model loaded during FastAPI startup.

## 40. What is top_k in semantic search?

Answer: top_k controls how many matching document chunks ChromaDB should retrieve.

Our SearchRequest model allows values from 1 to 10, with a default value of 5.

For example, top_k=5 requests the five closest matching chunks.

## 41. What is cosine distance?

Answer: Cosine distance measures how different two vectors are in terms of their direction.

Our ChromaDB collection uses cosine distance:

metadata={"hnsw:space": "cosine"}

A lower cosine distance indicates a closer match. It is not a percentage score.

## 42. Why does the search endpoint return HTTP 404?

Answer: The endpoint tries to retrieve the ChromaDB collection associated with the provided session ID.

If that collection does not exist, ChromaDB raises NotFoundError.

Our application catches this exception and returns HTTP 404 with an appropriate error message.

## 43. What information does our semantic search endpoint return?

Answer: The endpoint returns:

- Session ID
- Original search query
- Number of retrieved results
- Matching chunk IDs
- Retrieved document text
- Page numbers
- Chunk indexes
- Cosine distances

This allows the application to identify and use relevant document passages.

## 44. What is the difference between semantic search and RAG question answering?

Answer:

Semantic search retrieves relevant document chunks based on the meaning of a question.

RAG (Retrieval-Augmented Generation) uses retrieved document chunks as context for an LLM to generate a grounded answer.

Our application currently implements semantic retrieval. LLM-powered answer generation is the next major development milestone.

## 45. What happens when multiple PDFs are uploaded without restarting FastAPI?

Answer: Each upload creates a separate ChromaDB collection with a different session ID.

All collections remain available in memory while the same application process is running.

The user must provide the correct session ID to search the corresponding document.

## 46. Why does our ChromaDB data disappear after restarting FastAPI?

Answer: Our application uses chromadb.EphemeralClient(), which stores collections in memory.

When the application process terminates or restarts, the in-memory collections are lost.

Persistent storage has not yet been implemented.

## Updated Project Status

**Completed and tested:**

- Python virtual environment and dependency installation.
- FastAPI application and lifecycle management.
- Swagger/OpenAPI documentation.
- PDF validation and in-memory text extraction using PyMuPDF.
- Page-based text chunking with overlap.
- Sentence Transformer model loading through FastAPI lifespan.
- CPU-based embedding generation (384 dimensions).
- ChromaDB EphemeralClient initialization.
- UUID-based document collection creation.
- In-memory vector insertion and metadata storage.
- Pydantic request validation using BaseModel and Field.
- Semantic search API: `POST /documents/search`.
- Query embedding generation.
- ChromaDB vector similarity retrieval.
- Retrieval of matching document chunks, page numbers and cosine distances.
- Handling of missing document collections using HTTP 404.
- Successful Swagger testing with five retrieved search results.
- Semantic search implementation committed and pushed to GitHub.

**Still pending:**

- Session expiry and automatic collection cleanup.
- Persistent vector storage.
- Authentication and document ownership controls.
- LLM-based question answering using RAG.
- OCR support for scanned PDFs.
- Automated unit and API integration tests.
- Application-specific monitoring and observability.
- Security hardening and performance optimization.
- Dockerization and deployment.
- Final documentation and production-readiness review.

## Updated Interview Explanation

"I developed a Python REST API using FastAPI and Uvicorn for an AI-powered document assistant. I implemented PDF upload and validation, extracted text page by page using PyMuPDF, and divided the extracted content into overlapping chunks.

I integrated Sentence Transformers to generate 384-dimensional embeddings and used ChromaDB's EphemeralClient to store document vectors, text and metadata in memory.

I also implemented a semantic search API using Pydantic for request validation. The endpoint generates embeddings for user queries, retrieves the corresponding document collection using a session ID, and performs vector similarity search using ChromaDB. It returns relevant document chunks, page references and cosine distances.

I verified the PDF processing using a 30-page document that generated 54 chunks and 54 stored vectors. I also tested the semantic search endpoint successfully through Swagger UI.

The next major development milestone is integrating an LLM to generate grounded answers using Retrieval-Augmented Generation (RAG)."
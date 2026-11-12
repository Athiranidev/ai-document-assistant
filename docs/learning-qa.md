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

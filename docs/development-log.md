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

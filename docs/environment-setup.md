# AI Document Assistant — Environment Setup

This document records the Python environment, installed packages, installation commands and verification results from the beginning of the project.

## 1. Project environment

| Item | Observed value |
|---|---|
| Operating system | Ubuntu Linux |
| Python version | 3.14.4 |
| Virtual environment | `.venv` |
| Project directory | `~/DevOps/ai-document-assistant` |
| Execution device | CPU |
| CUDA available | False |
| GPU count | 0 |

## 2. Create the virtual environment

From the project root:

```bash
python3 -m venv .venv
```

This creates a project-specific Python environment.

### Why use a virtual environment?

- Keeps project packages separate from system Python.
- Prevents package changes from affecting other projects that use their own environments.
- Makes dependency management and project reproduction easier.

A virtual environment isolates Python packages, not CPU, RAM or disk usage.

## 3. Activate the virtual environment

On Ubuntu/Linux:

```bash
source .venv/bin/activate
```

Verify:

```bash
which python
python --version
```

Expected Python path:

```text
/home/<user>/DevOps/ai-document-assistant/.venv/bin/python
```

The terminal prompt should display `(.venv)`.

### Activating in a new terminal

```bash
cd ~/DevOps/ai-document-assistant
source .venv/bin/activate
```

The `.venv` directory remains after closing a terminal. It does not need to be recreated each time.

## 4. Packages installed

All packages below were installed into the project's `.venv`.

| Package | Observed version | Purpose |
|---|---:|---|
| FastAPI | 0.162.5 | Backend API framework |
| Uvicorn | 0.54.0 | ASGI server |
| python-multipart | 0.0.33 | Multipart PDF uploads |
| PyMuPDF | 2.1 | PDF reading and text extraction |
| Sentence Transformers | 6.3.0 | Text embedding generation |
| PyTorch | 2.15.0 | Machine-learning execution |
| Transformers | 5.22.2 | Transformer model components |
| ChromaDB | 1.5.9 | Vector storage and similarity search |

### Important supporting packages

The installations also resolved supporting dependencies, including:

- NumPy — numerical operations.
- SciPy — scientific computing.
- scikit-learn — machine-learning utilities.
- Hugging Face Hub — model downloads and caching.
- Tokenizers — text tokenization.
- ONNX Runtime — model execution support.
- gRPC and OpenTelemetry packages — ChromaDB dependencies.

These were installed or resolved as dependencies, not all selected directly by the application.

## 5. Installation commands used

### FastAPI and API dependencies

```bash
python -m pip install fastapi uvicorn python-multipart
```

### PDF extraction

```bash
python -m pip install pymupdf
```

### Embedding generation

```bash
python -m pip install sentence-transformers
```

### Vector database

```bash
python -m pip install chromadb==1.5.9
```

Use `python -m pip` with the project virtual environment active.

## 6. Verify installed packages

Check individual package versions:

```bash
python -m pip show fastapi
python -m pip show uvicorn
python -m pip show python-multipart
python -m pip show pymupdf
python -m pip show sentence-transformers
python -m pip show torch
python -m pip show transformers
python -m pip show chromadb
```

List all installed packages:

```bash
python -m pip list
```

Check dependency consistency:

```bash
python -m pip check
```

Verified output after ChromaDB installation:

```text
No broken requirements found.
```

## 7. Dependency snapshots

The environment was recorded at two points.

**Before ChromaDB installation:**

```text
docs/requirements-before-chromadb.txt
```

**Current complete dependency list:**

```text
requirements.lock.txt
```

Update the current lock file after intentional package changes:

```bash
python -m pip freeze > requirements.lock.txt
```

Recreate the environment on another machine:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.lock.txt
```

Review changes to the lock file before committing them.

## 8. Embedding model

Model:

```text
sentence-transformers/all-MiniLM-L6-v2
```

Purpose:

- Converts text into numerical vectors.
- Represents aspects of the meaning of each text chunk.
- Produces 384-dimensional embeddings.

Model loading used:

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer(
    "sentence-transformers/all-MiniLM-L6-v2",
    device="cpu"
)
```

The model was downloaded from Hugging Face and cached locally. Model files are separate from Python packages and are not included in the project repository.

### Verified embedding test

Two sample sentences were converted into vectors.

Observed output:

```text
Embedding shape: (2, 384)
Vector length: 384
Execution device: cpu
```

## 9. CPU and GPU verification

PyTorch reported:

```text
PyTorch: 2.15.0+cu132
CUDA available: False
GPU count: 0
```

We therefore selected CPU execution for the initial project implementation.

Both CPUs and GPUs can perform model inference. GPU acceleration can be considered later if the processing workload requires it and suitable GPU hardware is available.

## 10. ChromaDB in-memory storage

The project uses:

```python
import chromadb

client = chromadb.EphemeralClient()
```

Purpose:

- Store numerical embedding vectors.
- Associate vectors with their original text.
- Preserve document metadata.
- Retrieve semantically similar text later.

The ChromaDB client is initialized during FastAPI startup and made available through:

```python
app.state.chroma_client
```

Our current design uses temporary in-memory storage rather than persistent disk storage.

Important behaviour:

- The original PDF is not permanently saved.
- Browser refresh does not automatically delete server-side collections.
- ChromaDB data is lost when the application process terminates.
- Automatic session expiry and cleanup still need to be implemented.

## 11. Start the FastAPI application

From the project root, with `.venv` active:

```bash
uvicorn app.main:app --reload
```

Application address:

```text
http://127.0.0.1:8000
```

Useful URLs:

| URL | Purpose |
|---|---|
| `/` | Root endpoint |
| `/health` | Health-check endpoint |
| `/docs` | Swagger UI |
| `/openapi.json` | OpenAPI specification |

Full Swagger URL:

```text
http://127.0.0.1:8000/docs
```

### Two-terminal workflow

**Terminal 1:** Keep Uvicorn running.

**Terminal 2:** Run curl, package-management, Git and other development commands.

Activate `.venv` separately in each terminal.

Use `Ctrl+C` to stop Uvicorn. `Ctrl+Z` suspends it rather than terminating it.

## 12. Current application processing pipeline

```text
PDF upload
    |
    v
PDF validation
    |
    v
PyMuPDF text extraction
    |
    v
Text chunking
    |
    v
Sentence Transformers
    |
    v
384-dimensional embeddings
    |
    v
ChromaDB EphemeralClient
    |
    v
Temporary vector storage
```

### Verified end-to-end test

A 30-page text-based PDF was processed through Swagger.

| Metric | Observed result |
|---|---:|
| Page count | 30 |
| Extracted characters | 50,148 |
| Text chunks | 54 |
| Embeddings generated | 54 |
| Dimensions per embedding | 384 |
| Vectors stored in ChromaDB | 54 |
| HTTP response | 200 |

The application generated a unique document session ID and collection name.

## 13. Git exclusions

The project `.gitignore` contains:

```gitignore
.venv/
__pycache__/
*.py[cod]
.env
.pytest_cache/
.mypy_cache/
.coverage
```

Do not commit virtual environments, Python cache files, local secrets or downloaded model cache files.

## 14. Environment maintenance checklist

- [x] Python version verified.
- [x] Project virtual environment created.
- [x] Virtual environment activation verified.
- [x] FastAPI installed.
- [x] Uvicorn installed.
- [x] python-multipart installed.
- [x] PyMuPDF installed and tested.
- [x] Sentence Transformers installed and tested.
- [x] PyTorch installed and CPU execution verified.
- [x] ChromaDB installed and tested.
- [x] Dependency health checked using `pip check`.
- [x] Current dependency lock file generated.
- [x] PDF extraction tested.
- [x] Text chunking tested.
- [x] Embedding generation tested.
- [x] ChromaDB vector insertion tested.
- [ ] Semantic search implemented.
- [ ] Session expiry and automatic collection cleanup implemented.
- [ ] LLM integration implemented.
- [ ] OCR implemented for image-only PDFs.
- [ ] Automated tests and deployment completed.

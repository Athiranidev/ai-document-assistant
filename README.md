# AI Document Assistant

An AI-powered PDF question-answering application built using **Retrieval-Augmented Generation (RAG)**, FastAPI, Sentence Transformers, ChromaDB, and Google's Gemini API.

The application allows users to upload PDF documents, extract and process their content, generate embeddings, retrieve relevant information, and generate contextual answers using an LLM.

## 1. Project Overview

The AI Document Assistant follows a RAG architecture to answer questions based on uploaded PDF documents.

Instead of sending an entire document to the language model, the application retrieves relevant document chunks and uses them as context for answer generation.

### Key Features

- PDF document upload and processing.
- PDF text extraction using PyMuPDF.
- Text chunking with configurable chunk size and overlap.
- Semantic embeddings using Sentence Transformers.
- Persistent vector storage using ChromaDB.
- Similarity-based document retrieval.
- Contextual question answering using Google Gemini.
- Source references with page and chunk information.
- REST API development using FastAPI.
- Docker containerization.
- Persistent storage using Docker volumes.
- AWS EC2 deployment.

## 2. Technology Stack

| Component | Technology |
|---|---|
| Programming Language | Python 3.14 |
| Backend Framework | FastAPI |
| API Server | Uvicorn |
| PDF Processing | PyMuPDF |
| Embedding Model | all-MiniLM-L6-v2 |
| Vector Database | ChromaDB |
| Large Language Model | Google Gemini |
| Validation | Pydantic |
| Containerization | Docker |
| Cloud Platform | AWS EC2 |
| Operating System | Ubuntu Linux |
| Version Control | Git and GitHub |

## 3. Application Architecture

### RAG Workflow

1. User uploads a PDF document.
2. PyMuPDF extracts text from the PDF.
3. Extracted text is divided into smaller chunks.
4. Sentence Transformers generates vector embeddings.
5. ChromaDB stores document chunks and embeddings.
6. User submits a search query or question.
7. The application generates an embedding for the query.
8. ChromaDB retrieves the most relevant document chunks.
9. Retrieved content is passed to Google Gemini as context.
10. Gemini generates an answer based on the retrieved document content.
11. The API returns the answer and source references.

## 4. API Endpoints

The application exposes the following REST API endpoints.

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Application welcome message |
| GET | `/health` | Application health check |
| POST | `/documents/upload` | Upload and process PDF documents |
| POST | `/documents/search` | Retrieve relevant document chunks |
| POST | `/documents/ask` | Generate contextual answers using Gemini |

### API Documentation

FastAPI automatically generates interactive API documentation.

Once the application is running, access:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Document Upload

Endpoint: `POST /documents/upload`

- Accepts PDF files.
- Maximum file size: 10 MB.
- Extracts text and divides it into chunks.
- Generates embeddings.
- Stores vectors in ChromaDB.
- Returns a unique document session ID.

### Document Search

Endpoint: `POST /documents/search`

Request example:

```json
{
  "session_id": "YOUR_DOCUMENT_SESSION_ID",
  "query": "What is this document about?",
  "top_k": 5
}
```

Returns relevant document chunks with page numbers, chunk indexes, and similarity distances.

### Document Question Answering

Endpoint: `POST /documents/ask`

Request example:

```json
{
  "session_id": "YOUR_DOCUMENT_SESSION_ID",
  "question": "What are the main points in this document?",
  "top_k": 5
}
```

The application retrieves relevant content and sends it to Gemini for contextual answer generation.

Answers include source references such as `[S1]` and `[S2]`.

## 5. Project Structure

```text
ai-document-assistant/
│
├── app/
│   └── main.py
│
├── docs/
│   ├── aws-ec2-infrastructure-setup.md
│   └── aws-ec2-docker-deployment.md
│
├── storage/
│
├── Dockerfile
├── .dockerignore
├── .gitignore
├── .env
├── constraints-docker.txt
├── requirements-docker.txt
├── requirements.lock.txt
└── README.md
```

**Note:** The `.env` file and persistent storage are excluded from Git.

## 6. Environment Configuration

Create a `.env` file in the project root directory.

```env
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=your_supported_gemini_model
```

The application uses these environment variables to initialize the Gemini client.

Protect the API key and never commit `.env` to GitHub.

Set appropriate file permissions:

```bash
chmod 600 .env
```

## 7. Run the Application Using Docker

### Build the Docker Image

```bash
docker build -t ai-document-assistant:latest .
```

### Create a Persistent Volume

```bash
docker volume create ai-document-assistant-data
```

### Run the Container

```bash
docker run -d \
  --name ai-document-assistant \
  -p 127.0.0.1:8000:8000 \
  --env-file .env \
  -v ai-document-assistant-data:/app/storage \
  ai-document-assistant:latest
```

### Verify the Container

```bash
docker ps
```

### View Application Logs

```bash
docker logs -f ai-document-assistant
```

### Stop the Container

```bash
docker stop ai-document-assistant
```

### Remove the Container

```bash
docker rm ai-document-assistant
```

Removing the container does not remove the named Docker volume.

## 8. AWS EC2 Deployment

The application was deployed on an AWS EC2 Ubuntu instance.

**Deployment configuration:**

| Component | Configuration |
|---|---|
| Cloud Provider | Amazon Web Services |
| Region | Asia Pacific (Sydney) |
| Region Code | `ap-southeast-2` |
| Compute Service | Amazon EC2 |
| Operating System | Ubuntu |
| Container Runtime | Docker |
| Application Port | 8000 |
| Persistent Storage | Docker named volume |

### Deployment Process

1. Created and configured an EC2 instance.
2. Configured SSH access through a security group.
3. Connected to the Ubuntu server using SSH.
4. Installed Docker.
5. Cloned the GitHub repository.
6. Configured environment variables.
7. Built the Docker image on EC2.
8. Created a persistent Docker volume.
9. Started the application container.
10. Verified application startup and API endpoints.

### SSH Port Forwarding

The application was bound to the EC2 loopback interface.

Local access was configured through SSH port forwarding:

```bash
ssh -i /path/to/your-key.pem \
  -L 8000:127.0.0.1:8000 \
  ubuntu@YOUR_EC2_PUBLIC_IP
```

Access the application locally:

```text
http://localhost:8000/docs
```

**Current deployment state:** The EC2 instance is stopped to control AWS costs. The EBS root volume has been retained to preserve server data.

See the `docs/` directory for detailed AWS infrastructure and deployment documentation.

## 9. Security Considerations

- API keys are stored in environment variables.
- `.env` is excluded from Git.
- SSH access is restricted through security group rules.
- The application container binds to localhost on the EC2 host.
- Docker storage is maintained using a named volume.
- PDF uploads are restricted to a maximum of 10 MB.

## 10. Testing and Current Status

### Verified

- Application startup on EC2.
- Root endpoint.
- Health endpoint.
- Swagger UI access.
- PDF upload and processing.
- Document chunk generation.
- Embedding generation.
- ChromaDB persistence.
- Document search.
- Docker container deployment.

### Pending Verification

- End-to-end question answering through `/documents/ask`.
- Gemini response reliability and successful answer generation.

A Gemini API availability/model issue was encountered during testing. The complete question-answering workflow still requires final verification.

## 11. Future Improvements

- Improve LLM API error handling and retry mechanisms.
- Add request latency and error monitoring.
- Implement Prometheus and Grafana monitoring.
- Add authentication and authorization.
- Improve document session management.
- Add support for additional document formats.
- Automate Docker deployment.
- Implement CI/CD using GitHub Actions.

## 12. Project Status

**Development and AWS Docker deployment completed.**

The application has been deployed and its core document-processing and retrieval functionality has been tested.

Final end-to-end verification of Gemini-powered question answering remains pending.

---


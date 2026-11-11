# System Architecture

## 1. Architecture Overview

The AI Document Assistant follows a modular architecture.

The application consists of four main layers:

1. Application Layer
2. Document Processing and RAG Layer
3. LLM Integration Layer
4. Monitoring and Operations Layer

The system uses FastAPI for API development, Python for document processing,
a vector database for semantic retrieval, and an LLM API for answer generation.

Docker Compose will manage the application services.

## 2. High-Level Architecture

```mermaid
flowchart TD
    U[User] --> API[FastAPI Application]

    API --> UP[PDF Upload]
    UP --> EX[Text Extraction]
    EX --> CH[Text Chunking]
    CH --> EM[Embedding Generation]
    EM --> DB[(Vector Database)]

    U --> Q[User Question]
    Q --> API
    API --> RET[Semantic Retrieval]
    DB --> RET
    RET --> LLM[LLM API]
    LLM --> ANS[Generated Answer]
    ANS --> U

    API --> LOG[Structured Logging]
    API --> MET[Application Metrics]
    MET --> PROM[Prometheus]
    PROM --> GRAF[Grafana]

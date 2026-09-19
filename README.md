# RAG Scholar — Multi-Agent Learning Assistant

Local-first RAG application for studying from PDF courses, combining **FastAPI, Ollama, ChromaDB, embeddings and specialized AI agents**.

## Main project

See the full implementation in **rag-learning-assistant/**.

### Core capabilities

- PDF upload and text extraction
- Chunking with page metadata
- Local embeddings with **nomic-embed-text**
- Persistent vector search with **ChromaDB**
- Multi-agent routing for different user intents
- Grounded RAG answers with file/page sources
- Course summaries
- Automatically generated 5-question quizzes
- Sliding conversation memory
- General chat mode
- FastAPI REST API and web interface

## Architecture

```mermaid
flowchart LR
    UI["Web UI<br/>HTML · CSS · JavaScript"] --> API["FastAPI Backend<br/>REST API"]
    UI -->|"PDF upload"| API
    API -->|"chat request"| ROUTER["Router Agent<br/>Rules / Regex<br/>LLM fallback"]
    ROUTER -->|"answer / summary / quiz"| RAG["RAG Agent"]
    ROUTER -->|"general"| GENERAL["General Agent"]
    API <--> MEMORY["Memory Agent<br/>Sliding history"]
    MEMORY --> RAG
    MEMORY --> GENERAL
    API -->|"background indexing"| PDF["PDF Processor<br/>PyMuPDF<br/>chunking + page metadata"]
    PDF --> VS["ChromaDB<br/>Persistent Vector Store<br/>Cosine similarity · Top-K"]
    RAG -->|"retrieve chunks"| VS
    VS -->|"embeddings"| OLLAMA["Ollama<br/>Local LLM + Embeddings"]
    ROUTER -->|"ambiguous intent"| OLLAMA
    RAG -->|"grounded generation"| OLLAMA
    GENERAL -->|"generation"| OLLAMA
```

## Screenshots

### Main interface

![RAG Scholar UI](rag-learning-assistant/docs/images/ui_overview.png)

### RAG answer with sources

![RAG answer](rag-learning-assistant/docs/images/rag-answer.png)

### Quiz mode

![Quiz mode](rag-learning-assistant/docs/images/quiz-mode.png)

### PDF indexing

![PDF indexing](rag-learning-assistant/docs/images/pdf-indexing.png)

## Stack

**Python · FastAPI · Ollama · ChromaDB · PyMuPDF · Embeddings · RAG · AI Agents · REST API**

For installation, configuration, REST endpoints and the full technical explanation, see the project README in **rag-learning-assistant/**.
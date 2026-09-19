# RAG Scholar — Multi-Agent Learning Assistant

### Local-first RAG application for interactive learning from PDF courses

RAG Scholar is a local AI learning assistant that combines **Retrieval-Augmented Generation (RAG)** with a **multi-agent architecture**. Students can upload course PDFs, ask questions grounded in those documents, generate summaries and create interactive quizzes.

Built with **FastAPI, Ollama, ChromaDB, PyMuPDF and Python**.

## What the project demonstrates

- **RAG pipeline:** PDF → text extraction → chunking → embeddings → vector retrieval → grounded generation
- **Multi-agent routing:** a Router Agent selects the appropriate agent and mode
- **Source grounding:** answers expose the source file and page used by retrieval
- **Conversational memory:** recent turns are retained and injected into the LLM context
- **Local LLM inference:** chat and embeddings run through Ollama
- **Web application:** REST API + browser-based interface

## Architecture

![RAG Scholar architecture](docs/images/architecture.svg)

### Logical flow

```text
PDF Upload
    ↓
Text Extraction (PyMuPDF)
    ↓
Chunking + Page Metadata
    ↓
Embeddings (nomic-embed-text)
    ↓
ChromaDB Vector Store
    ↓
User Query
    ↓
Router Agent
    ├── RAG Agent → answer / summary / quiz
    ├── General Agent → general conversation
    └── Memory Agent → conversation context
    ↓
Ollama Local LLM
    ↓
Grounded Response + Sources
```

## Multi-Agent Architecture

### Router Agent

Acts as the entry point for intent detection. It uses fast rule-based classification first and an **LLM fallback** for ambiguous requests.

Supported routes:

| Intent | Agent | Mode |
|---|---|---|
| Course question | RAG Agent | answer |
| Summary request | RAG Agent | summary |
| Practice request | RAG Agent | quiz |
| General conversation | General Agent | general |

### RAG Agent

Implements the retrieval-augmented generation workflow:

1. Retrieve the most relevant chunks from ChromaDB
2. Build a document context
3. Inject the context into the LLM prompt
4. Generate a grounded response
5. Return source file, page and similarity information

### Memory Agent

Maintains a sliding window of recent conversation turns and provides context to the LLM for conversational continuity.

### General Agent

Handles general questions that do not require document retrieval.

## RAG Pipeline

### Document ingestion

PDF documents are processed with **PyMuPDF**. Text is extracted page by page and divided into overlapping chunks.

Default configuration:

```text
Chunk size       : 512 words
Chunk overlap    : 64 words
Top-K retrieval  : 5 chunks
```

Page metadata is preserved so retrieved information can be traced back to the original document.

### Embeddings and retrieval

Embeddings are generated locally with:

```text
nomic-embed-text
```

ChromaDB stores the vectors using cosine similarity and retrieves the most relevant chunks for each query.

### Generation

Ollama provides the local LLM used for:

- grounded answers
- summaries
- quiz generation
- intent classification when rule-based routing is ambiguous

## Features

### RAG answer

- Ask questions about uploaded courses
- Generate answers from retrieved document context
- Display source filename and page

### Summary

- Generate structured summaries from course content
- Highlight key concepts and important points

### Quiz

- Generate exactly five multiple-choice questions
- Return answers and explanations
- Interactive answer checking in the web interface

### Memory

- Sliding conversation history
- Recent context injected into LLM prompts
- Ability to clear the current session history

## Web Interface

The frontend provides:

- Automatic agent routing
- Explicit answer / summary / quiz modes
- PDF upload and document management
- Chat history
- Source display
- Interactive quizzes
- Ollama / API health status

### Recommended portfolio screenshots

Add the following real screenshots under `docs/images/`:

| File | What it should show |
|---|---|
| `ui-overview.png` | Main RAG Scholar interface |
| `rag-answer.png` | RAG answer with displayed source and page |
| `quiz-mode.png` | Generated quiz and answer feedback |
| `pdf-indexing.png` | Uploaded PDF visible in the document list |
| `swagger.png` | FastAPI interactive API documentation |

These screenshots should show the actual running application rather than mockups.

## Project Structure

```text
rag-learning-assistant/
├── backend/
│   ├── agents/
│   │   ├── router.py
│   │   ├── rag_agent.py
│   │   ├── memory_agent.py
│   │   └── general_agent.py
│   ├── core/
│   │   ├── ollama_client.py
│   │   ├── vector_store.py
│   │   └── pdf_processor.py
│   ├── config.py
│   └── main.py
├── frontend/
│   └── index.html
├── data/
│   ├── uploads/
│   └── vectorstore/
├── docs/
│   └── images/
│       └── architecture.svg
├── requirements.txt
├── start.sh
├── commandes.txt
└── README.md
```

## Technology Stack

| Layer | Technologies |
|---|---|
| Language | Python |
| API | FastAPI · Uvicorn |
| LLM | Ollama |
| Embeddings | nomic-embed-text |
| RAG | Retrieval-Augmented Generation |
| Vector Store | ChromaDB |
| PDF Processing | PyMuPDF |
| Agents | Router · RAG · Memory · General |
| Validation / Retry | Pydantic · Tenacity |
| Frontend | HTML · CSS · JavaScript |

## Installation

### Requirements

- Python 3.11+
- Ollama
- Sufficient RAM for the selected local LLM

### Install Python dependencies

```bash
python -m venv .venv

# Linux / macOS
source .venv/bin/activate

# Windows
.venv\\Scripts\\activate

pip install -r requirements.txt
```

### Download Ollama models

```bash
ollama pull llama3.2:3b
ollama pull nomic-embed-text
```

### Start the application

```bash
ollama serve
python -m uvicorn backend.main:app --reload --port 8000
```

Open:

- `http://localhost:8000` — Web application
- `http://localhost:8000/docs` — Swagger UI
- `http://localhost:8000/redoc` — ReDoc

## Configuration

Main settings are defined in `backend/config.py` and can be overridden through `.env`.

```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b
OLLAMA_EMBED_MODEL=nomic-embed-text
CHUNK_SIZE=512
CHUNK_OVERLAP=64
TOP_K=5
MAX_HISTORY_TURNS=10
API_HOST=0.0.0.0
API_PORT=8000
```

## REST API

Main endpoints:

```text
POST   /chat
POST   /documents/upload
GET    /documents
DELETE /documents/{filename}
GET    /memory
DELETE /memory
GET    /health
```

Interactive documentation is available through Swagger UI at `/docs` when the application is running.

## Academic Context

Project developed for the **IA Distribuée & Systèmes Multi-Agents** module.

The project focuses on applying RAG, local LLM inference and agent-based orchestration to an educational use case.

## License

Academic project.
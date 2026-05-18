"""
RAG Learning Assistant — API FastAPI
Point d'entrée principal
"""
import shutil
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from loguru import logger

from backend.config import settings
from backend.agents.router import router_agent
from backend.agents.rag_agent import rag_agent
from backend.agents.general_agent import general_agent
from backend.agents.memory_agent import memory_agent
from backend.core.vector_store import vector_store
from backend.core.pdf_processor import pdf_processor
from backend.core.ollama_client import ollama_client

# ------------------------------------------------------------------ #
#  Application                                                         #
# ------------------------------------------------------------------ #
app = FastAPI(
    title="RAG Learning Assistant",
    description="Assistant pédagogique basé sur RAG et Ollama",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Servir le frontend statique
frontend_dir = Path(__file__).parent.parent / "frontend"
if frontend_dir.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")


# ------------------------------------------------------------------ #
#  Schémas Pydantic                                                    #
# ------------------------------------------------------------------ #
class ChatRequest(BaseModel):
    message: str
    mode: Literal["auto", "answer", "summary", "quiz"] = "auto"


class ChatResponse(BaseModel):
    agent: str
    mode: str | None
    answer: str
    sources: list[dict]
    quiz: list[dict] | None
    history_turns: int


class HealthResponse(BaseModel):
    status: str
    ollama: dict
    model_in_use: str
    documents: list[str]
    total_chunks: int
    history_turns: int


# ------------------------------------------------------------------ #
#  Routes                                                              #
# ------------------------------------------------------------------ #

@app.get("/", include_in_schema=False)
async def serve_frontend():
    index = frontend_dir / "index.html"
    if index.exists():
        return FileResponse(str(index))
    return {"message": "RAG Learning Assistant API — voir /docs"}


@app.get("/health", response_model=HealthResponse)
async def health():
    """Statut du système."""
    ollama_status = await ollama_client.health_check()
    return HealthResponse(
        status="ok",
        ollama=ollama_status,
        model_in_use=settings.OLLAMA_MODEL,
        documents=vector_store.list_sources(),
        total_chunks=vector_store.count(),
        history_turns=memory_agent.turn_count,
    )


# ------------------------------------------------------------------ #
#  Chat                                                                #
# ------------------------------------------------------------------ #
@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """Point d'entrée principal du chatbot."""
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Le message est vide.")

    # Enregistrer la question dans la mémoire
    memory_agent.add_user_message(req.message)

    # Router
    force_mode = None if req.mode == "auto" else req.mode
    routing = await router_agent.route(req.message, force_mode=force_mode)

    # Dispatch
    if routing["agent"] == "rag":
        result = await rag_agent.run(req.message, mode=routing["mode"])
    else:
        result = await general_agent.run(req.message)

    # Enregistrer la réponse dans la mémoire
    memory_agent.add_assistant_message(
        result["answer"], agent_used=result["agent"]
    )

    return ChatResponse(
        agent=result["agent"],
        mode=result.get("mode"),
        answer=result["answer"],
        sources=result.get("sources", []),
        quiz=result.get("quiz"),
        history_turns=memory_agent.turn_count,
    )


# ------------------------------------------------------------------ #
#  Documents                                                           #
# ------------------------------------------------------------------ #
@app.post("/documents/upload")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
):
    """Téléverse et indexe un PDF."""
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Seuls les fichiers PDF sont acceptés.")

    # Sauvegarde
    dest = settings.UPLOAD_DIR / file.filename
    with dest.open("wb") as f:
        shutil.copyfileobj(file.file, f)
    logger.info(f"PDF reçu : {file.filename} ({dest.stat().st_size / 1024:.1f} Ko)")

    # Indexation en arrière-plan
    background_tasks.add_task(_index_pdf, dest)

    return {
        "message": f"'{file.filename}' reçu et indexation en cours…",
        "filename": file.filename,
    }


async def _index_pdf(pdf_path: Path):
    """Indexe un PDF dans le vector store (tâche de fond)."""
    try:
        chunks = pdf_processor.process(pdf_path)
        added = await vector_store.add_chunks(chunks)
        logger.success(f"Indexé {added} chunks depuis {pdf_path.name}")
    except Exception as e:
        logger.error(f"Erreur d'indexation pour {pdf_path.name} : {e}")


@app.get("/documents")
async def list_documents():
    """Liste les documents indexés."""
    sources = vector_store.list_sources()
    return {"documents": sources, "total_chunks": vector_store.count()}


@app.delete("/documents/{filename}")
async def delete_document(filename: str):
    """Supprime un document du vector store."""
    deleted = vector_store.delete_source(filename)
    pdf_path = settings.UPLOAD_DIR / filename
    if pdf_path.exists():
        pdf_path.unlink()
    return {"deleted_chunks": deleted, "filename": filename}


# ------------------------------------------------------------------ #
#  Mémoire                                                             #
# ------------------------------------------------------------------ #
@app.get("/memory")
async def get_memory():
    """Retourne l'historique de conversation."""
    return {
        "history": memory_agent.get_full_history(),
        "stats": memory_agent.stats,
    }


@app.delete("/memory")
async def clear_memory():
    """Réinitialise l'historique."""
    memory_agent.clear()
    return {"message": "Historique réinitialisé."}


# ------------------------------------------------------------------ #
#  Démarrage                                                           #
# ------------------------------------------------------------------ #
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True,
    )

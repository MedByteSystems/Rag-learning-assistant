"""
Agent RAG — Retrieval-Augmented Generation sur les cours PDF
Modes : réponse précise | résumé | quiz
"""
from loguru import logger
from backend.core.ollama_client import ollama_client
from backend.core.vector_store import vector_store
from backend.agents.memory_agent import memory_agent
from backend.config import settings

# ------------------------------------------------------------------ #
#  Prompts système                                                     #
# ------------------------------------------------------------------ #

ANSWER_SYSTEM = """Tu es un assistant pédagogique expert. Tu réponds UNIQUEMENT à partir des extraits de cours fournis.
Si la réponse n'est pas dans les extraits, dis-le honnêtement.
Cite la source (nom du fichier et numéro de page) pour chaque information importante.
Réponds en français, de façon structurée et pédagogique."""

SUMMARY_SYSTEM = """Tu es un assistant pédagogique expert en synthèse.
À partir des extraits fournis, produis un résumé clair et structuré en français.
Utilise des titres, des listes à puces et des explications concises.
Mets en évidence les concepts-clés et les points importants."""

QUIZ_SYSTEM = """Tu es un professeur qui crée des QCM d'entraînement.
À partir des extraits de cours fournis, génère exactement 5 questions à choix multiples en JSON.
Format STRICT (JSON uniquement, sans markdown) :
[
  {
    "question": "...",
    "options": ["A) ...", "B) ...", "C) ...", "D) ..."],
    "correct": "A",
    "explanation": "..."
  }
]
Les questions doivent couvrir des concepts importants du cours."""


class RAGAgent:
    """
    Agent RAG : récupère les chunks pertinents depuis ChromaDB
    et génère une réponse augmentée avec le LLM Ollama.
    """

    # ------------------------------------------------------------------ #
    #  Point d'entrée principal                                            #
    # ------------------------------------------------------------------ #
    async def run(self, query: str, mode: str = "answer") -> dict:
        logger.info(f"[RAGAgent:{mode}] '{query[:60]}…'")

        # 1. Récupérer les chunks pertinents
        chunks = await vector_store.search(query, top_k=settings.TOP_K)

        if not chunks:
            return {
                "agent": "rag",
                "mode": mode,
                "answer": (
                    "Aucun document n'est encore indexé. "
                    "Veuillez d'abord téléverser vos cours PDF."
                ),
                "sources": [],
                "quiz": None,
            }

        # 2. Construire le contexte documentaire
        context = self._build_context(chunks)

        # 3. Dispatcher selon le mode
        if mode == "summary":
            return await self._run_summary(query, context, chunks)
        elif mode == "quiz":
            return await self._run_quiz(query, context, chunks)
        else:
            return await self._run_answer(query, context, chunks)

    # ------------------------------------------------------------------ #
    #  Mode : Réponse précise                                              #
    # ------------------------------------------------------------------ #
    async def _run_answer(self, query: str, context: str, chunks: list[dict]) -> dict:
        history_ctx = memory_agent.get_context_summary()

        prompt = f"""Historique récent de la conversation :
{history_ctx}

Extraits de cours pertinents :
{context}

Question de l'étudiant : {query}

Réponds de manière précise et pédagogique en te basant sur les extraits ci-dessus."""

        answer = await ollama_client.chat(
            messages=[{"role": "user", "content": prompt}],
            system=ANSWER_SYSTEM,
            temperature=0.3,
        )
        return {
            "agent": "rag",
            "mode": "answer",
            "answer": answer,
            "sources": self._format_sources(chunks),
            "quiz": None,
        }

    # ------------------------------------------------------------------ #
    #  Mode : Résumé                                                        #
    # ------------------------------------------------------------------ #
    async def _run_summary(self, query: str, context: str, chunks: list[dict]) -> dict:
        sujet = query if query else "Résume l'ensemble"
        prompt = f"""Extraits de cours à résumer :
{context}

Sujet ou filtre de l'étudiant : {sujet}

Produis un résumé structuré et complet."""

        answer = await ollama_client.chat(
            messages=[{"role": "user", "content": prompt}],
            system=SUMMARY_SYSTEM,
            temperature=0.4,
        )
        return {
            "agent": "rag",
            "mode": "summary",
            "answer": answer,
            "sources": self._format_sources(chunks),
            "quiz": None,
        }

    # ------------------------------------------------------------------ #
    #  Mode : Quiz                                                          #
    # ------------------------------------------------------------------ #
    async def _run_quiz(self, query: str, context: str, chunks: list[dict]) -> dict:
        import json

        prompt = f"""Extraits de cours pour le quiz :
{context}

Thème du quiz (si précisé) : {query if query else 'Général'}

Génère 5 questions QCM en JSON uniquement."""

        raw = await ollama_client.chat(
            messages=[{"role": "user", "content": prompt}],
            system=QUIZ_SYSTEM,
            temperature=0.6,
        )

        # Nettoyage et parsing JSON
        quiz_data = self._parse_quiz_json(raw)

        return {
            "agent": "rag",
            "mode": "quiz",
            "answer": "Quiz généré avec succès ! Bonne chance 🎓",
            "sources": self._format_sources(chunks[:2]),
            "quiz": quiz_data,
        }

    # ------------------------------------------------------------------ #
    #  Helpers                                                              #
    # ------------------------------------------------------------------ #
    @staticmethod
    def _build_context(chunks: list[dict]) -> str:
        parts = []
        for i, c in enumerate(chunks, 1):
            parts.append(
                f"[Extrait {i} — {c['source']}, page {c['page']} "
                f"(pertinence: {c['score']:.2f})]\n{c['text']}"
            )
        return "\n\n---\n\n".join(parts)

    @staticmethod
    def _format_sources(chunks: list[dict]) -> list[dict]:
        seen = set()
        sources = []
        for c in chunks:
            key = (c["source"], c["page"])
            if key not in seen:
                seen.add(key)
                sources.append({
                    "file": c["source"],
                    "page": c["page"],
                    "score": c["score"],
                })
        return sources

    @staticmethod
    def _parse_quiz_json(raw: str) -> list[dict] | None:
        import re, json
        # Chercher un tableau JSON dans la réponse
        match = re.search(r"\[.*\]", raw, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        logger.warning("Impossible de parser le JSON du quiz")
        return None


rag_agent = RAGAgent()
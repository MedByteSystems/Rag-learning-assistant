"""
Router — Cerveau du système multi-agents
Analyse l'intention de l'utilisateur et route vers le bon agent.
"""
import re
from loguru import logger
from backend.core.ollama_client import ollama_client
from backend.core.vector_store import vector_store

# ------------------------------------------------------------------ #
#  Classification par règles (rapide, sans LLM)                       #
# ------------------------------------------------------------------ #

QUIZ_PATTERNS = [
    r"\bquiz\b", r"\bqcm\b", r"\bquestion[s]?\b.*\bcours\b",
    r"\btest[e]?\b", r"\bentraîn", r"\binterrog", r"\bexamen\b",
]

SUMMARY_PATTERNS = [
    r"\brésum[eé]\b", r"\bsynthèse\b", r"\bsynthétis", r"\bsummar",
    r"\brésum[eé]r\b", r"\bprincipaux points\b", r"\bidées clés\b",
    r"\bvue d.ensemble\b",
]

RAG_PATTERNS = [
    r"\bselon le cours\b", r"\bdans le pdf\b", r"\bdans le document\b",
    r"\bd.après le cours\b", r"\bexplique.*cours\b", r"\bque dit\b",
    r"\bchapitre\b", r"\bpoly[copié]*\b",
]

GENERAL_PATTERNS = [
    r"\bbonjour\b", r"\bmerci\b", r"\bsalut\b", r"\bcomment ça va\b",
    r"\bc.est quoi\b", r"\bqu.est[-\s]ce que\b", r"\baidez?[-\s]moi\b",
]


class RouterAgent:
    """
    Analyse l'intention utilisateur et route vers :
    - rag_agent (mode: answer | summary | quiz)  — si documents disponibles
    - general_agent                               — conversation générale
    """

    async def route(self, query: str, force_mode: str | None = None) -> dict:
        """
        Retourne un dict {agent, mode} indiquant quel agent appeler.
        force_mode permet à l'UI de forcer quiz/summary/answer.
        """
        query_lower = query.lower().strip()
        has_documents = vector_store.count() > 0

        # --- Mode forcé par l'UI ---
        if force_mode in ("quiz", "summary", "answer"):
            if has_documents:
                logger.info(f"[Router] Mode forcé : rag/{force_mode}")
                return {"agent": "rag", "mode": force_mode}
            else:
                logger.info("[Router] Mode forcé mais pas de docs → general")
                return {"agent": "general", "mode": None}

        # --- Classification par règles ---
        if has_documents:
            if self._matches(query_lower, QUIZ_PATTERNS):
                logger.info("[Router] → rag/quiz (règle)")
                return {"agent": "rag", "mode": "quiz"}
            if self._matches(query_lower, SUMMARY_PATTERNS):
                logger.info("[Router] → rag/summary (règle)")
                return {"agent": "rag", "mode": "summary"}
            if self._matches(query_lower, RAG_PATTERNS):
                logger.info("[Router] → rag/answer (règle)")
                return {"agent": "rag", "mode": "answer"}

        if self._matches(query_lower, GENERAL_PATTERNS):
            logger.info("[Router] → general (règle salutation)")
            return {"agent": "general", "mode": None}

        # --- Fallback LLM pour les cas ambigus ---
        if has_documents:
            intent = await self._llm_classify(query)
            logger.info(f"[Router] LLM intent → {intent}")
            if intent in ("quiz", "summary", "answer"):
                return {"agent": "rag", "mode": intent}

        logger.info("[Router] → general (fallback)")
        return {"agent": "general", "mode": None}

    # ------------------------------------------------------------------ #
    #  Classification LLM (cas ambigus)                                    #
    # ------------------------------------------------------------------ #
    async def _llm_classify(self, query: str) -> str:
        """Utilise le LLM pour classifier l'intention (answer/summary/quiz/general)."""
        prompt = f"""Classe cette question d'un étudiant en exactement UN seul mot parmi :
- answer    (question précise sur un cours)
- summary   (demande de résumé ou synthèse)
- quiz      (demande de questions d'entraînement)
- general   (question générale sans lien avec un document)

Question : "{query}"

Réponds UNIQUEMENT avec le mot choisi, rien d'autre."""

        try:
            result = await ollama_client.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
            )
            word = result.strip().lower().split()[0]
            if word in ("answer", "summary", "quiz", "general"):
                return word
        except Exception as e:
            logger.warning(f"LLM classify failed: {e}")
        return "answer"

    # ------------------------------------------------------------------ #
    #  Helper                                                              #
    # ------------------------------------------------------------------ #
    @staticmethod
    def _matches(text: str, patterns: list[str]) -> bool:
        return any(re.search(p, text, re.IGNORECASE) for p in patterns)


router_agent = RouterAgent()

"""
Agent Mémoire — gestion de l'historique conversationnel
"""
from collections import deque
from datetime import datetime
from loguru import logger
from backend.config import settings


class MemoryAgent:
    """
    Maintient un historique glissant de la conversation.
    Sert de contexte pour les autres agents.
    """

    def __init__(self, max_turns: int = settings.MAX_HISTORY_TURNS):
        self.max_turns = max_turns
        self._history: deque[dict] = deque(maxlen=max_turns * 2)  # user + assistant
        self._session_start = datetime.now()

    # ------------------------------------------------------------------ #
    #  Écriture                                                             #
    # ------------------------------------------------------------------ #
    def add_user_message(self, content: str) -> None:
        self._history.append({
            "role": "user",
            "content": content,
            "timestamp": datetime.now().isoformat(),
        })

    def add_assistant_message(self, content: str, agent_used: str = "general") -> None:
        self._history.append({
            "role": "assistant",
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "agent": agent_used,
        })

    # ------------------------------------------------------------------ #
    #  Lecture                                                              #
    # ------------------------------------------------------------------ #
    def get_messages_for_llm(self) -> list[dict]:
        """Retourne l'historique au format attendu par Ollama (role/content)."""
        return [
            {"role": msg["role"], "content": msg["content"]}
            for msg in self._history
        ]

    def get_context_summary(self) -> str:
        """Résumé textuel de l'historique pour injection dans un prompt."""
        if not self._history:
            return "Aucun historique disponible."
        lines = []
        for msg in list(self._history)[-6:]:  # 3 derniers échanges
            role = "Étudiant" if msg["role"] == "user" else "Assistant"
            lines.append(f"{role}: {msg['content'][:200]}")
        return "\n".join(lines)

    def get_full_history(self) -> list[dict]:
        """Historique complet pour l'UI."""
        return list(self._history)

    # ------------------------------------------------------------------ #
    #  Utilitaires                                                          #
    # ------------------------------------------------------------------ #
    def clear(self) -> None:
        self._history.clear()
        logger.info("Historique réinitialisé")

    @property
    def turn_count(self) -> int:
        return len(self._history) // 2

    @property
    def stats(self) -> dict:
        return {
            "turns": self.turn_count,
            "messages": len(self._history),
            "session_start": self._session_start.isoformat(),
        }


# Instance partagée (une session = un MemoryAgent)
memory_agent = MemoryAgent()

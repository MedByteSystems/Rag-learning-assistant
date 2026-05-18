"""
Agent Général — conversation basique sans RAG
"""
from loguru import logger
from backend.core.ollama_client import ollama_client
from backend.agents.memory_agent import memory_agent

SYSTEM_PROMPT = """Tu es un assistant pédagogique intelligent spécialisé dans l'aide aux étudiants.
Tu réponds en français de manière claire, structurée et encourageante.
Tu peux expliquer des concepts, répondre à des questions générales et guider l'étudiant.
Si une question porte sur un document PDF, indique à l'étudiant d'utiliser le mode RAG."""


class GeneralAgent:
    """Agent de conversation généraliste (sans accès aux documents)."""

    async def run(self, query: str) -> dict:
        logger.info(f"[GeneralAgent] Traitement : {query[:60]}…")

        # Historique conversationnel
        messages = memory_agent.get_messages_for_llm()
        messages.append({"role": "user", "content": query})

        response = await ollama_client.chat(
            messages=messages,
            system=SYSTEM_PROMPT,
            temperature=0.7,
        )

        return {
            "agent": "general",
            "answer": response,
            "sources": [],
        }


general_agent = GeneralAgent()

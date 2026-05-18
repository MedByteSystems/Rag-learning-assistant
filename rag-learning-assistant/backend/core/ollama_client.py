"""
Client Ollama — interface avec le LLM local
"""
import httpx
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_fixed
from backend.config import settings


class OllamaClient:
    """Encapsule les appels à l'API Ollama locale."""

    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = settings.OLLAMA_MODEL
        self.embed_model = settings.OLLAMA_EMBED_MODEL

    # ------------------------------------------------------------------ #
    #  Chat                                                                 #
    # ------------------------------------------------------------------ #
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
    async def chat(
        self,
        messages: list[dict],
        system: str = "",
        temperature: float = 0.7,
        stream: bool = False,
    ) -> str:
        """Envoie une conversation à Ollama et retourne la réponse complète."""
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": stream,
            "options": {"temperature": temperature},
        }
        if system:
            payload["system"] = system

        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                f"{self.base_url}/api/chat",
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            return data["message"]["content"]

    # ------------------------------------------------------------------ #
    #  Embeddings                                                           #
    # ------------------------------------------------------------------ #
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
    async def embed(self, text: str) -> list[float]:
        """Génère un vecteur d'embedding pour un texte."""
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{self.base_url}/api/embeddings",
                json={"model": self.embed_model, "prompt": text},
            )
            resp.raise_for_status()
            return resp.json()["embedding"]

    # ------------------------------------------------------------------ #
    #  Santé                                                                #
    # ------------------------------------------------------------------ #
    async def health_check(self) -> dict:
        """Vérifie qu'Ollama est disponible et liste les modèles."""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(f"{self.base_url}/api/tags")
                resp.raise_for_status()
                models = [m["name"] for m in resp.json().get("models", [])]
                return {"status": "ok", "models": models}
        except Exception as e:
            logger.error(f"Ollama non disponible : {e}")
            return {"status": "error", "message": str(e)}


# Instance partagée
ollama_client = OllamaClient()

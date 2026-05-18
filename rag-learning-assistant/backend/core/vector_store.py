"""
Vector Store — ChromaDB + embeddings Ollama (nomic-embed-text)
"""
import asyncio
from pathlib import Path
from loguru import logger
import chromadb
from chromadb.config import Settings as ChromaSettings

from backend.config import settings
from backend.core.pdf_processor import Chunk


class VectorStore:
    """
    Encapsule ChromaDB pour stocker et rechercher des chunks de documents.
    Les embeddings sont générés par Ollama (nomic-embed-text) en local.
    """

    def __init__(self):
        self._client = chromadb.PersistentClient(
            path=str(settings.VECTORSTORE_DIR),
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self._collection = self._client.get_or_create_collection(
            name="cours",
            metadata={"hnsw:space": "cosine"},
        )
        logger.info(
            f"VectorStore initialisé — {self._collection.count()} chunks stockés"
        )

    # ------------------------------------------------------------------ #
    #  Indexation                                                           #
    # ------------------------------------------------------------------ #
    async def add_chunks(self, chunks: list[Chunk]) -> int:
        """
        Ajoute des chunks dans ChromaDB.
        Les embeddings sont produits via Ollama de manière asynchrone.
        """
        from backend.core.ollama_client import ollama_client

        ids, docs, metas, embeds = [], [], [], []

        for chunk in chunks:
            # Skip si déjà indexé
            if self._exists(chunk.chunk_id):
                continue
            embedding = await ollama_client.embed(chunk.text)
            ids.append(chunk.chunk_id)
            docs.append(chunk.text)
            metas.append(chunk.metadata)
            embeds.append(embedding)

        if ids:
            self._collection.add(
                ids=ids,
                documents=docs,
                metadatas=metas,
                embeddings=embeds,
            )
            logger.info(f"Ajouté {len(ids)} nouveaux chunks au vector store")

        return len(ids)

    # ------------------------------------------------------------------ #
    #  Recherche                                                            #
    # ------------------------------------------------------------------ #
    async def search(self, query: str, top_k: int = settings.TOP_K) -> list[dict]:
        """
        Retourne les top_k chunks les plus pertinents pour une requête.
        """
        from backend.core.ollama_client import ollama_client

        query_embedding = await ollama_client.embed(query)
        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, self._collection.count() or 1),
            include=["documents", "metadatas", "distances"],
        )

        hits = []
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            hits.append(
                {
                    "text": doc,
                    "source": meta.get("source", "inconnu"),
                    "page": meta.get("page", 0),
                    "score": round(1 - dist, 4),   # Cosine similarity
                }
            )
        return hits

    # ------------------------------------------------------------------ #
    #  Utilitaires                                                          #
    # ------------------------------------------------------------------ #
    def _exists(self, chunk_id: str) -> bool:
        try:
            res = self._collection.get(ids=[chunk_id])
            return len(res["ids"]) > 0
        except Exception:
            return False

    def list_sources(self) -> list[str]:
        """Liste les noms de fichiers indexés."""
        if self._collection.count() == 0:
            return []
        all_metas = self._collection.get(include=["metadatas"])["metadatas"]
        return sorted(set(m.get("source", "") for m in all_metas))

    def delete_source(self, source_name: str) -> int:
        """Supprime tous les chunks d'un fichier source."""
        results = self._collection.get(
            where={"source": source_name}, include=["metadatas"]
        )
        ids = results["ids"]
        if ids:
            self._collection.delete(ids=ids)
        logger.info(f"Supprimé {len(ids)} chunks de '{source_name}'")
        return len(ids)

    def count(self) -> int:
        return self._collection.count()


vector_store = VectorStore()

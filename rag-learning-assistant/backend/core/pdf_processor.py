"""
Traitement des PDFs — extraction et découpage en chunks
"""
import re
from pathlib import Path
from dataclasses import dataclass, field
import fitz  # PyMuPDF
from loguru import logger
from backend.config import settings


@dataclass
class Chunk:
    """Un morceau de texte extrait d'un PDF."""
    text: str
    source: str          # Nom du fichier
    page: int
    chunk_id: str
    metadata: dict = field(default_factory=dict)


class PDFProcessor:
    """Extrait le texte d'un PDF et le découpe en chunks avec chevauchement."""

    def __init__(
        self,
        chunk_size: int = settings.CHUNK_SIZE,
        chunk_overlap: int = settings.CHUNK_OVERLAP,
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    # ------------------------------------------------------------------ #
    #  Extraction                                                           #
    # ------------------------------------------------------------------ #
    def extract_text_by_page(self, pdf_path: Path) -> list[dict]:
        """Retourne une liste de {page, text} pour chaque page du PDF."""
        pages = []
        doc = fitz.open(str(pdf_path))
        for page_num, page in enumerate(doc, start=1):
            text = page.get_text("text")
            text = self._clean_text(text)
            if text.strip():
                pages.append({"page": page_num, "text": text})
        doc.close()
        logger.info(f"Extrait {len(pages)} pages depuis {pdf_path.name}")
        return pages

    # ------------------------------------------------------------------ #
    #  Découpage                                                            #
    # ------------------------------------------------------------------ #
    def chunk_pages(self, pages: list[dict], source_name: str) -> list[Chunk]:
        """Découpe les pages en chunks de taille fixe avec chevauchement."""
        chunks: list[Chunk] = []
        full_text_with_markers = []

        # Concatène tout en gardant les numéros de page
        for p in pages:
            full_text_with_markers.append((p["page"], p["text"]))

        # Fenêtre glissante sur les mots
        words_with_pages = []
        for page_num, text in full_text_with_markers:
            for word in text.split():
                words_with_pages.append((word, page_num))

        step = self.chunk_size - self.chunk_overlap
        for i, start in enumerate(range(0, len(words_with_pages), step)):
            window = words_with_pages[start : start + self.chunk_size]
            if not window:
                break
            text = " ".join(w for w, _ in window)
            page = window[0][1]  # Page du premier mot
            chunk = Chunk(
                text=text,
                source=source_name,
                page=page,
                chunk_id=f"{source_name}_chunk_{i:04d}",
                metadata={"source": source_name, "page": page, "chunk_index": i},
            )
            chunks.append(chunk)

        logger.info(f"Créé {len(chunks)} chunks pour {source_name}")
        return chunks

    # ------------------------------------------------------------------ #
    #  Nettoyage                                                            #
    # ------------------------------------------------------------------ #
    @staticmethod
    def _clean_text(text: str) -> str:
        text = re.sub(r"\s+", " ", text)
        text = re.sub(r"[^\x20-\x7E\u00C0-\u024F\n]", "", text)
        return text.strip()

    # ------------------------------------------------------------------ #
    #  Pipeline complet                                                     #
    # ------------------------------------------------------------------ #
    def process(self, pdf_path: Path) -> list[Chunk]:
        """Pipeline complet : PDF → chunks."""
        pages = self.extract_text_by_page(pdf_path)
        return self.chunk_pages(pages, source_name=pdf_path.name)


pdf_processor = PDFProcessor()

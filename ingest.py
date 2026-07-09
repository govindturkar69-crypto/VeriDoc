"""
Phase 2 — Document Ingestion.

Loads PDFs, Word files, text and HTML from the documents/ folder,
extracts clean text (with OCR fallback for scanned PDFs), and splits
it into overlapping passages ("chunks") ready for embedding.

Run directly to preview what will be ingested:
    python ingest.py
"""
from __future__ import annotations
import re
from pathlib import Path
from dataclasses import dataclass

import config


@dataclass
class Chunk:
    """One passage of text plus where it came from (for citations)."""
    text: str
    source: str      # file name
    page: int        # page number (0 if not applicable)
    chunk_id: str    # unique id


# ---------------------------------------------------------------- loaders
def _clean(text: str) -> str:
    """Collapse whitespace and strip junk so chunks are tidy."""
    text = text.replace("\x00", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _load_pdf(path: Path) -> list[tuple[int, str]]:
    """Return [(page_number, text), ...]. Falls back to OCR on empty pages."""
    import fitz  # PyMuPDF
    pages = []
    doc = fitz.open(path)
    for i, page in enumerate(doc, start=1):
        text = page.get_text().strip()
        if len(text) < 20:                      # likely a scanned image page
            text = _ocr_page(page)
        pages.append((i, _clean(text)))
    doc.close()
    return pages


def _ocr_page(page) -> str:
    """OCR a single PDF page. Needs Tesseract installed on the system."""
    try:
        import pytesseract
        from PIL import Image
        import io
        pix = page.get_pixmap(dpi=200)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        return pytesseract.image_to_string(img)
    except Exception as e:
        print(f"    [OCR skipped: {e}]")
        return ""


def _load_docx(path: Path) -> list[tuple[int, str]]:
    import docx
    d = docx.Document(path)
    text = "\n".join(p.text for p in d.paragraphs)
    return [(0, _clean(text))]


def _load_txt(path: Path) -> list[tuple[int, str]]:
    return [(0, _clean(path.read_text(encoding="utf-8", errors="ignore")))]


def _load_html(path: Path) -> list[tuple[int, str]]:
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(path.read_text(encoding="utf-8", errors="ignore"), "html.parser")
    for tag in soup(["script", "style"]):
        tag.decompose()
    return [(0, _clean(soup.get_text(separator="\n")))]


LOADERS = {
    ".pdf": _load_pdf,
    ".docx": _load_docx,
    ".txt": _load_txt,
    ".md": _load_txt,
    ".html": _load_html,
    ".htm": _load_html,
}


# ---------------------------------------------------------------- chunking
def _chunk_text(text: str, size: int, overlap: int) -> list[str]:
    """Simple sliding-window chunker that tries to break on paragraph/space."""
    if not text:
        return []
    chunks, start = [], 0
    n = len(text)
    while start < n:
        end = min(start + size, n)
        # try to end on a natural boundary (only when not at the very end)
        if end < n:
            boundary = text.rfind("\n", start, end)
            if boundary == -1 or boundary <= start + size // 2:
                boundary = text.rfind(" ", start, end)
            if boundary > start:
                end = boundary
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= n:          # reached the end — stop (prevents tail-fragment spam)
            break
        start = max(end - overlap, start + 1)
    return chunks


# ---------------------------------------------------------------- public API
def load_documents(folder: Path | None = None) -> list[Chunk]:
    """Load every supported file in the folder and return a list of Chunks."""
    folder = folder or config.DOCUMENTS_DIR
    folder = Path(folder)
    all_chunks: list[Chunk] = []

    files = [f for f in sorted(folder.glob("*")) if f.suffix.lower() in LOADERS]
    if not files:
        print(f"No documents found in {folder}. Add some PDFs/DOCX and re-run.")
        return all_chunks

    for f in files:
        print(f"Loading {f.name} ...")
        try:
            pages = LOADERS[f.suffix.lower()](f)
        except Exception as e:
            print(f"    [failed to load: {e}]")
            continue
        for page_num, text in pages:
            for j, piece in enumerate(_chunk_text(text, config.CHUNK_SIZE, config.CHUNK_OVERLAP)):
                cid = f"{f.name}::p{page_num}::c{j}"
                all_chunks.append(Chunk(text=piece, source=f.name, page=page_num, chunk_id=cid))

    print(f"\nIngested {len(all_chunks)} chunks from {len(files)} file(s).")
    return all_chunks


if __name__ == "__main__":
    chunks = load_docu
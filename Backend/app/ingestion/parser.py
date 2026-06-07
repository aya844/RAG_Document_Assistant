import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def parse_file(file_path: str) -> list[dict]:
    """
    Returns a list of pages:
    [{"page_number": int, "content": str}, ...]
    """
    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix == ".pdf":
        return _parse_pdf(file_path)
    elif suffix == ".txt":
        return _parse_txt(file_path)
    else:
        raise ValueError(f"Unsupported file type: {suffix}")


def _parse_pdf(file_path: str) -> list[dict]:
    try:
        import fitz  # PyMuPDF
        pages = []
        doc = fitz.open(file_path)
        for i, page in enumerate(doc):
            text = page.get_text("text").strip()
            if text:
                pages.append({"page_number": i + 1, "content": text})
        doc.close()
        logger.info(f"PyMuPDF parsed {len(pages)} pages from {file_path}")
        return pages
    except Exception as e:
        logger.warning(f"PyMuPDF failed ({e}), falling back to pypdf")
        return _parse_pdf_fallback(file_path)


def _parse_pdf_fallback(file_path: str) -> list[dict]:
    from pypdf import PdfReader
    reader = PdfReader(file_path)
    pages = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        text = text.strip()
        if text:
            pages.append({"page_number": i + 1, "content": text})
    logger.info(f"pypdf fallback parsed {len(pages)} pages")
    return pages


def _parse_txt(file_path: str) -> list[dict]:
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read().strip()
    # TXT has no pages — treat entire file as page 1
    return [{"page_number": 1, "content": content}]
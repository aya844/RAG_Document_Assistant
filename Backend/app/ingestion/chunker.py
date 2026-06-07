import uuid
from dataclasses import dataclass
from app.config import get_settings

settings = get_settings()


@dataclass
class ParentChunk:
    id: str
    document_id: str
    content: str
    chunk_index: int
    page_number: int | None


@dataclass
class ChildChunk:
    id: str
    document_id: str
    parent_id: str
    content: str
    chunk_index: int
    page_number: int | None


def _split_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    """
    Simple word-boundary splitter.
    Avoids LangChain dependency for this utility.
    """
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start += chunk_size - overlap
    return chunks


def create_parent_child_chunks(
    pages: list[dict],
    document_id: str,
) -> tuple[list[ParentChunk], list[ChildChunk]]:
    """
    Strategy:
    1. Split each page into parent chunks (~1200 words)
    2. Split each parent into child chunks (~300 words, 50 overlap)
    3. Child chunks carry parent_id for later context retrieval
    """
    parents: list[ParentChunk] = []
    children: list[ChildChunk] = []

    parent_index = 0
    child_index = 0

    for page in pages:
        page_number = page["page_number"]
        content = page["content"]

        # Split page into parent chunks
        parent_texts = _split_text(
            content,
            chunk_size=settings.parent_chunk_size,
            overlap=0,  # No overlap for parents — they're context windows, not search units
        )

        for parent_text in parent_texts:
            if len(parent_text.strip()) < 50:  # Skip near-empty chunks
                continue

            parent_id = str(uuid.uuid4())
            parent = ParentChunk(
                id=parent_id,
                document_id=document_id,
                content=parent_text,
                chunk_index=parent_index,
                page_number=page_number,
            )
            parents.append(parent)
            parent_index += 1

            # Split parent into child chunks
            child_texts = _split_text(
                parent_text,
                chunk_size=settings.child_chunk_size,
                overlap=settings.child_chunk_overlap,
            )

            for child_text in child_texts:
                if len(child_text.strip()) < 30:
                    continue

                child = ChildChunk(
                    id=str(uuid.uuid4()),
                    document_id=document_id,
                    parent_id=parent_id,
                    content=child_text,
                    chunk_index=child_index,
                    page_number=page_number,
                )
                children.append(child)
                child_index += 1

    return parents, children
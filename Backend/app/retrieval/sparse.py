import pickle
import os
import logging
from dataclasses import dataclass
from rank_bm25 import BM25Okapi
from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


@dataclass
class BM25Document:
    chunk_id: str       # child chunk id
    parent_id: str
    document_id: str
    content: str
    page_number: int | None


class BM25Index:
    def __init__(self):
        self.documents: list[BM25Document] = []
        self.bm25: BM25Okapi | None = None

    def add_documents(self, docs: list[BM25Document]):
        self.documents.extend(docs)
        self._rebuild()

    def _rebuild(self):
        if not self.documents:
            return
        tokenized = [doc.content.lower().split() for doc in self.documents]
        self.bm25 = BM25Okapi(tokenized)

    def search(
            self,
            query: str,
            top_k: int,
            document_ids: list[str] | None = None,
    ) -> list[tuple[BM25Document, float]]:
        """
        document_ids: restrict search to these document IDs.
        Empty list or None = search all documents.
        """
        if not self.bm25 or not self.documents:
            return []

        tokenized_query = query.lower().split()

        if document_ids:
            # Filter to subset, build temporary BM25 index
            subset = [d for d in self.documents if d.document_id in document_ids]
            if not subset:
                return []
            from rank_bm25 import BM25Okapi
            tmp = BM25Okapi([d.content.lower().split() for d in subset])
            scores = tmp.get_scores(tokenized_query)
            top_indices = sorted(
                range(len(scores)), key=lambda i: scores[i], reverse=True
            )[:top_k]
            return [(subset[i], float(scores[i])) for i in top_indices]

        # No filter — search entire index
        scores = self.bm25.get_scores(tokenized_query)
        top_indices = sorted(
            range(len(scores)), key=lambda i: scores[i], reverse=True
        )[:top_k]
        return [(self.documents[i], float(scores[i])) for i in top_indices]

    def save(self):
        os.makedirs(os.path.dirname(settings.bm25_index_path), exist_ok=True)
        with open(settings.bm25_index_path, "wb") as f:
            pickle.dump(self, f)
        logger.info(f"BM25 index saved: {len(self.documents)} documents")

    @classmethod
    def load(cls) -> "BM25Index":
        if os.path.exists(settings.bm25_index_path):
            with open(settings.bm25_index_path, "rb") as f:
                index = pickle.load(f)
            logger.info(f"BM25 index loaded: {len(index.documents)} documents")
            return index
        return cls()


# Module-level singleton — loaded once at startup
_bm25_index: BM25Index | None = None


def get_bm25_index() -> BM25Index:
    global _bm25_index
    if _bm25_index is None:
        _bm25_index = BM25Index.load()
    return _bm25_index
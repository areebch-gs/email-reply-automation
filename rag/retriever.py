from rag.embedder import Embedder
from rag.store import VectorStore


class Retriever:
    def __init__(self, embedder: Embedder, store: VectorStore):
        self.embedder = embedder
        self.store = store

    def search(self, query: str, top_k: int = 5, language: str | None = None) -> list[dict]:
        embedding = self.embedder.embed([query])[0]
        return self.store.query(embedding, top_k=top_k, language=language)

import chromadb

COLLECTION_NAME = "finance_docs"


class VectorStore:
    def __init__(self, persist_dir: str = "./chroma_db"):
        self.client = chromadb.PersistentClient(path=persist_dir)
        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

    def upsert(self, chunks: list[dict], embeddings: list[list[float]]) -> None:
        self.collection.upsert(
            ids=[c["id"] for c in chunks],
            embeddings=embeddings,
            documents=[c["text"] for c in chunks],
            metadatas=[
                {"source": c["source"], "page": c["page"], "language": c.get("language", "english")}
                for c in chunks
            ],
        )

    def query(self, embedding: list[float], top_k: int = 5, language: str | None = None) -> list[dict]:
        where = {"language": language} if language else None
        results = self.collection.query(
            query_embeddings=[embedding],
            n_results=top_k,
            where=where,
            include=["documents", "metadatas", "distances"],
        )
        chunks = []
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            chunks.append({"text": doc, "source": meta["source"], "page": meta["page"], "score": 1 - dist})
        return chunks

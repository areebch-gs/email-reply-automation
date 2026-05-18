from openai import OpenAI

EMBEDDING_MODEL = "text-embedding-3-small"


class Embedder:
    def __init__(self, client: OpenAI):
        self.client = client

    def embed(self, texts: list[str]) -> list[list[float]]:
        response = self.client.embeddings.create(model=EMBEDDING_MODEL, input=texts)
        return [item.embedding for item in response.data]

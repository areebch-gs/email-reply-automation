from openai import OpenAI

CHAT_MODEL = "gpt-4o-mini"

SYSTEM_PROMPT = (
    "You are a finance support assistant. "
    "Answer the vendor's question using only the provided context from internal finance guides. "
    "If the answer is not in the context, say you don't have enough information. "
    "Be concise and professional."
)


class Generator:
    def __init__(self, client: OpenAI):
        self.client = client

    def generate(self, query: str, context_chunks: list[dict]) -> str:
        context = "\n\n".join(
            f"[{c['source']} — page {c['page']}]\n{c['text']}"
            for c in context_chunks
        )
        user_message = f"Context:\n{context}\n\nQuestion: {query}"
        response = self.client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
        )
        return response.choices[0].message.content

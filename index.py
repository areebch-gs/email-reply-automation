import os
from dotenv import load_dotenv
from openai import OpenAI
from rag.loader import load_pdfs
from rag.embedder import Embedder
from rag.store import VectorStore

load_dotenv()

PDF_FOLDER = "./fwdfinaiusecasesandnextsteps"

def main():
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    embedder = Embedder(client)
    store = VectorStore()

    print("Loading PDFs...")
    chunks = load_pdfs(PDF_FOLDER)
    print(f"  {len(chunks)} chunks loaded from {PDF_FOLDER}")

    print("Generating embeddings...")
    texts = [c["text"] for c in chunks]
    embeddings = embedder.embed(texts)
    print(f"  {len(embeddings)} embeddings generated")

    print("Storing in ChromaDB...")
    store.upsert(chunks, embeddings)
    print("  Done. Index ready.")


if __name__ == "__main__":
    main()

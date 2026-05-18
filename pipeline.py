import os
from dotenv import load_dotenv
from openai import OpenAI
from oracle.client import OracleAPClient
from rag.embedder import Embedder
from rag.store import VectorStore
from rag.retriever import Retriever
from rag.generator import Generator
from agents import email_agent

load_dotenv()

_client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
_embedder = Embedder(_client)
_store = VectorStore()
_retriever = Retriever(_embedder, _store)
_generator = Generator(_client)
_oracle = OracleAPClient()

# Maps the recipient mailbox prefix to the language used for RAG filtering
MAILBOX_LANGUAGE: dict[str, str] = {
    "ukaccountspayable":    "english",
    "uklonaccountspayable": "english",
    "deaccountspayable":    "german",
    "fraccountspayable":    "french",
    "noaccountspayable":    "english",  # no Norwegian docs, fallback to English
    "itaccountspayable":    "italian",
}


def _resolve_language(mailbox: str) -> str:
    """Extract the language from a full mailbox address or prefix."""
    prefix = mailbox.split("@")[0].lower().strip()
    return MAILBOX_LANGUAGE.get(prefix, "english")


def answer(query: str, top_k: int = 5) -> dict:
    """RAG-only lookup. Used for direct knowledge base questions."""
    chunks = _retriever.search(query, top_k=top_k)
    response = _generator.generate(query, chunks)
    sources = [{"file": c["source"], "page": c["page"]} for c in chunks]
    return {"answer": response, "sources": sources}


def process_email(email_body: str, mailbox: str = "ukaccountspayable@sharkninja.com") -> dict:
    """
    Full agent pipeline for vendor emails.

    Args:
        email_body - the raw email text
        mailbox    - the recipient mailbox the email was sent to (determines which language
                     docs to retrieve from the knowledge base)

    Returns:
        reply        - drafted response
        confidence   - 0.0–1.0
        needs_review - True = send to human approval queue
        tools_called - audit log of API calls made
        language     - language used for RAG filtering
    """
    language = _resolve_language(mailbox)
    result = email_agent.run(_client, _oracle, _retriever, email_body, language)
    result["language"] = language
    return result

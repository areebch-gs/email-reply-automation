import os
import pdfplumber

# Maps each supported language to its authoritative source documents.
# Add new languages or files here as the document library grows.
LANGUAGE_DOCS: dict[str, list[str]] = {
    "english": [
        "How to Get Paid Guide (UK).pdf",
        "How to Get Paid Guide (LDN).pdf",
        "New Supplier Set Up.pdf",
        "Responsibility of a PO Owner (UK).pdf",
        "Useful Finance Contacts (UK).pdf",
        "Sundry Creditors - usage policy .pdf",
        "Why has my supplier not been paid - troubleshooting guide.pdf",
    ],
    "german": [
        "How to Get Paid Guide (DE).pdf",
    ],
    "french": [
        "How to Get Paid Guide (FR).pdf",
    ],
    "italian": [
        "How to Get Paid Guide (IT Translated).pdf",
        "New Supplier Set Up (IT Translated).pdf",
        "Responsibility of a PO Owner (IT Translated).pdf",
        "Useful Finance Contacts (IT Translated).pdf",
    ],
    "spanish": [
        "New Supplier Set Up (ES Translated).pdf",
        "Responsibility of a PO Owner (ES Translated).pdf",
        "Useful Finance Contacts (ES Translated).pdf",
    ],
}

_FALLBACK_LANGUAGE = "english"


class ContextLoader:
    """
    Loads full document content for a given language directly into LLM context.

    This bypasses vector retrieval entirely — every document associated with
    the language is loaded and returned as a single context block. Documents
    are read from disk once and cached in memory for the lifetime of the instance.

    Use this when the document set per language is small enough to fit in context
    (typically < 20 pages total), which avoids semantic retrieval misses.
    """

    def __init__(self, docs_folder: str) -> None:
        self._docs_folder = docs_folder
        self._cache: dict[str, list[tuple[int, str]]] = {}  # filename -> [(page_num, text)]

    def get_context(self, language: str) -> tuple[str, list[dict]]:
        """
        Return (context_text, sources) for all docs registered under `language`.

        Falls back to English if the language has no registered documents.

        Returns:
            context_text  - all pages concatenated, ready to inject into the LLM prompt
            sources       - list of {"file": ..., "page": ...} for every page included
        """
        filenames = LANGUAGE_DOCS.get(language)
        if not filenames:
            filenames = LANGUAGE_DOCS[_FALLBACK_LANGUAGE]

        sections: list[str] = []
        sources: list[dict] = []

        for filename in filenames:
            pages = self._load_file(filename)
            for page_num, text in pages:
                sections.append(f"[{filename} — page {page_num}]\n{text}")
                sources.append({"file": filename, "page": page_num})

        context_text = "\n\n---\n\n".join(sections)
        return context_text, sources

    def languages(self) -> list[str]:
        """Return all languages that have registered documents."""
        return list(LANGUAGE_DOCS.keys())

    def _load_file(self, filename: str) -> list[tuple[int, str]]:
        """Load a PDF from disk and cache its pages. Returns [(page_num, text)]."""
        if filename in self._cache:
            return self._cache[filename]

        path = os.path.join(self._docs_folder, filename)
        pages: list[tuple[int, str]] = []

        with pdfplumber.open(path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                text = page.extract_text()
                if text and text.strip():
                    pages.append((page_num, text.strip()))

        self._cache[filename] = pages
        return pages

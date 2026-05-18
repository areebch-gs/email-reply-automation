# Email Reply Automation

An AI-powered agent that automatically drafts replies to vendor/supplier emails for an accounts payable team. It combines live Oracle AP data with a RAG knowledge base of internal finance guides to produce accurate, professional responses in the vendor's language.

## How It Works

```
Incoming email
      │
      ▼
 Detect language       ← from recipient mailbox address
 (via pipeline.py)
      │
      ▼
 LLM Agent loop        ← GPT-4o-mini with tool use
      │
      ├── search_invoices        → Oracle AP (live invoice status)
      ├── get_installments       → Oracle AP (payment schedule)
      └── search_knowledge_base  → ChromaDB (finance guides, filtered by language)
      │
      ▼
 Draft reply + metadata
 { reply, confidence, needs_review, tools_called, kb_sources }
```

The agent decides which tools to call based on the email content. A single email may trigger multiple tool calls. If confidence < 0.75 or the query can't be fully answered, `needs_review` is set to `true` for human approval.

## Project Structure

```
├── agents/
│   └── email_agent.py       # LLM agent loop with tool execution
├── rag/
│   ├── loader.py            # PDF ingestion + language tagging
│   ├── embedder.py          # OpenAI text-embedding-3-small
│   ├── store.py             # ChromaDB vector store with language filter
│   └── retriever.py         # Combines embedder + store
├── oracle/
│   ├── client.py            # Oracle AP REST client
│   └── queries.py           # search_invoices, get_invoice_installments
├── pipeline.py              # Entry point: process_email() and answer()
├── index.py                 # One-time script to build the vector index
├── ask.py                   # CLI for direct knowledge base queries
├── fwdfinaiusecasesandnextsteps/  # Source PDF documents
└── chroma_db/               # Persisted vector index (git-ignored)
```

## Language Routing

Docs are indexed with a language tag derived from their filename suffix:

| Filename suffix | Language |
|---|---|
| `(DE)` | German |
| `(FR)` | French |
| `(IT Translated)` | Italian |
| `(ES Translated)` | Spanish |
| `(UK)`, `(LDN)`, no suffix | English |

The recipient mailbox determines which language's docs are queried:

| Mailbox prefix | Language |
|---|---|
| `ukaccountspayable` | English |
| `uklonaccountspayable` | English |
| `deaccountspayable` | German |
| `fraccountspayable` | French |
| `itaccountspayable` | Italian |
| `noaccountspayable` | English (fallback) |

## Setup

### 1. Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure environment

Create a `.env` file:

```
OPENAI_API_KEY=sk-...
ORACLE_AP_BASE_URL=https://your-oracle-instance/...
ORACLE_AP_USERNAME=...
ORACLE_AP_PASSWORD=...
```

### 3. Build the vector index

Run once to embed all PDFs and store them in ChromaDB:

```bash
python index.py
```

## Usage

### Process a vendor email

```python
from pipeline import process_email

result = process_email(
    email_body="Hi, can you confirm when invoice INV-1234 will be paid?",
    mailbox="ukaccountspayable@yourcompany.com"
)

print(result["reply"])
print(result["kb_sources"])   # which finance docs were used
print(result["confidence"])
print(result["needs_review"])
```

### Direct knowledge base query

```bash
python ask.py "How do I set up a new supplier?"
```

## Response Format

`process_email()` returns:

| Field | Type | Description |
|---|---|---|
| `reply` | str | Drafted email response |
| `confidence` | float | 0.0–1.0 agent confidence score |
| `needs_review` | bool | True if human approval recommended |
| `tools_called` | list | Audit log of every tool call made |
| `kb_sources` | list | Finance docs used: `[{"file": "...", "page": N}]` |
| `language` | str | Language used for RAG filtering |

## Tech Stack

- **LLM**: GPT-4o-mini (OpenAI)
- **Embeddings**: text-embedding-3-small (OpenAI)
- **Vector store**: ChromaDB (cosine similarity)
- **PDF parsing**: pdfplumber
- **Live data**: Oracle AP REST API

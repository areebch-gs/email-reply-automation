import json
import os
from oracle.client import OracleAPClient
from oracle.queries import search_invoices, get_invoice_installments
from rag.retriever import Retriever  # kept for future use / A-B testing
from rag.context_loader import ContextLoader

_DOCS_FOLDER = os.path.join(os.path.dirname(__file__), "..", "fwdfinaiusecasesandnextsteps")
_context_loader = ContextLoader(_DOCS_FOLDER)

CHAT_MODEL = "gpt-4o-mini"
MAX_TOOL_ROUNDS = 6

SYSTEM_PROMPT = """You are a finance support assistant for an accounts payable team.
Your job is to help vendors and suppliers by answering their queries accurately and professionally.

Rules:
- Always reply in the same language the vendor used in their email.
- Never guess or make up invoice status, payment dates, or amounts — use the tools to get real data.
- When you find an invoice, always follow up with get_installments to retrieve the exact due date and payment schedule.
- Use search_knowledge_base for procedural questions (how to change payment terms, PO process, etc.) or to add context alongside Oracle data.
- A single email may need multiple tool calls — use as many as needed to give a complete answer.
- Always address every part of the vendor's question in your reply — if they asked multiple things, answer each one explicitly.
- Never ask the vendor for more information or follow-up questions. Always attempt to answer using the available tools first. Only if the tools return no relevant data should you state that you could not find the information.
- Be concise, professional, and empathetic in your reply.
- If you cannot find an answer to a specific part of the question after searching, only then say you don't have that information.

After your reply, on a new line output exactly this JSON (nothing else after it):
{"confidence": <0.0-1.0>, "needs_review": <true|false>}

Set needs_review to true if: the invoice was not found, the query is ambiguous, you could not fully answer, or confidence is below 0.75."""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_invoices",
            "description": (
                "Search Oracle AP for invoices by invoice number and/or supplier. "
                "Use when the vendor asks about invoice payment status, when they will be paid, "
                "or anything related to a specific invoice or payment."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "invoice_number": {
                        "type": "string",
                        "description": "Invoice number mentioned in the email",
                    },
                    "supplier_name": {
                        "type": "string",
                        "description": "Supplier or vendor company name",
                    },
                    "supplier_number": {
                        "type": "string",
                        "description": "Supplier number if explicitly mentioned",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_installments",
            "description": (
                "Fetch the payment schedule for a specific invoice. "
                "Always call this after finding an invoice — it gives the exact due date, "
                "scheduled payment date, and remaining amount."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "invoice_id": {
                        "type": "integer",
                        "description": "The InvoiceId returned by search_invoices",
                    },
                },
                "required": ["invoice_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_knowledge_base",
            "description": (
                "Search the internal finance guides and policy documents. "
                "Use for procedural questions (how to change payment terms, PO changes, supplier setup process) "
                "or to add process context alongside live Oracle data."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Natural language search query",
                    },
                },
                "required": ["query"],
            },
        },
    },
]


def _execute_tool(
    name: str,
    args: dict,
    oracle: OracleAPClient,
    retriever: Retriever,
    language: str,
    kb_sources: list,
) -> str:
    if name == "search_invoices":
        results = search_invoices(oracle, **args)
        if not results:
            return "No invoices found matching the provided criteria."
        return json.dumps(results, default=str)

    if name == "get_installments":
        results = get_invoice_installments(oracle, args["invoice_id"])
        if not results:
            return "No installment data found for this invoice."
        return json.dumps(results, default=str)

    if name == "search_knowledge_base":
        # Direct full-document load — bypasses vector retrieval.
        # Switch back to retriever.search() below if semantic search is needed.
        context_text, sources = _context_loader.get_context(language)
        # sources = retriever.search(args["query"], top_k=4, language=language)
        if not context_text:
            return "No relevant information found in the knowledge base."
        for entry in sources:
            if entry not in kb_sources:
                kb_sources.append(entry)
        return context_text

    return f"Unknown tool: {name}"


def run(
    provider,
    oracle: OracleAPClient,
    retriever: Retriever,
    email_body: str,
    language: str = "english",
) -> dict:
    """
    Process a vendor email and return a drafted reply with metadata.

    Returns:
        reply        - the drafted response text
        confidence   - 0.0–1.0 score from the agent
        needs_review - whether a human should review before sending
        tools_called - list of tool names + args used (for audit/logging)
        kb_sources   - knowledge base documents used to generate the reply
    """
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": email_body},
    ]
    tools_called = []
    kb_sources: list = []
    final_response = None

    for _ in range(MAX_TOOL_ROUNDS):
        response = provider.chat(messages, tools=TOOLS)
        final_response = response

        messages.append(response.assistant_message())

        if not response.tool_calls:
            break

        for tc in response.tool_calls:
            tool_id, name, args = response.parse_tool_call(tc)
            tools_called.append({"tool": name, "args": args})

            result = _execute_tool(name, args, oracle, retriever, language, kb_sources)
            messages.append(response.tool_result_message(tool_id, result))

    raw = final_response.content or ""

    # Parse the metadata JSON block the agent appends at the end
    reply_text = raw
    confidence = 0.5
    needs_review = True

    if '{"confidence"' in raw:
        body, _, tail = raw.rpartition('{"confidence"')
        try:
            meta = json.loads('{"confidence"' + tail)
            reply_text = body.strip()
            confidence = meta.get("confidence", 0.5)
            needs_review = meta.get("needs_review", True)
        except json.JSONDecodeError:
            pass

    return {
        "reply": reply_text,
        "confidence": confidence,
        "needs_review": needs_review,
        "tools_called": tools_called,
        "kb_sources": kb_sources,
    }

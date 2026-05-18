import streamlit as st
from pipeline import process_email

SAMPLE_QUESTIONS = {
    "Invoice status (UK)": (
        "Hi, I submitted invoice 14000 back in December and it still hasn't been paid. "
        "Can you let me know the status and when I can expect payment? Thanks",
        "ukaccountspayable@sharkninja.com",
    ),
    "PO change process (UK)": (
        "Hello, I need to make a change to one of my purchase orders but the system won't let me. "
        "How do I do this?",
        "ukaccountspayable@sharkninja.com",
    ),
    "PO change process (DE)": (
        "Hallo, ich kann meine Bestellung nicht ändern. Wie mache ich das?",
        "deaccountspayable@sharkninja.com",
    ),
    "Invoice status + payment process (UK) — Oracle & KB": (
        "Hi, invoice 14000 still hasn't been paid. Can you tell me the status and also explain "
        "what your standard payment terms are and how I get paid?",
        "ukaccountspayable@sharkninja.com",
    ),
}

MAILBOXES = [
    "ukaccountspayable@sharkninja.com",
    "uklonaccountspayable@sharkninja.com",
    "deaccountspayable@sharkninja.com",
    "fraccountspayable@sharkninja.com",
    "itaccountspayable@sharkninja.com",
    "noaccountspayable@sharkninja.com",
]

st.set_page_config(page_title="AP Email Assistant", page_icon="📧", layout="wide")

st.title("📧 Accounts Payable Email Assistant")
st.caption("AI-powered vendor email reply drafting — powered by Oracle AP + internal finance guides")

st.divider()

# ── Inputs ────────────────────────────────────────────────────────────────────
col1, col2 = st.columns([2, 1])

with col1:
    sample = st.selectbox(
        "Sample questions",
        options=["— type your own below —"] + list(SAMPLE_QUESTIONS.keys()),
    )

with col2:
    if sample != "— type your own below —":
        default_mailbox = SAMPLE_QUESTIONS[sample][1]
        mailbox_index = MAILBOXES.index(default_mailbox)
    else:
        mailbox_index = 0

    mailbox = st.selectbox("Recipient mailbox", options=MAILBOXES, index=mailbox_index)

default_email = (
    SAMPLE_QUESTIONS[sample][0]
    if sample != "— type your own below —"
    else ""
)

email_body = st.text_area(
    "Vendor email",
    value=default_email,
    height=140,
    placeholder="Paste or type the vendor's email here...",
)

submit = st.button("Generate Reply", type="primary", disabled=not email_body.strip())

st.divider()

# ── Processing + Results ──────────────────────────────────────────────────────
if submit and email_body.strip():
    with st.spinner("Processing..."):
        result = process_email(email_body, mailbox=mailbox)

    # Reply
    st.subheader("Drafted Reply")
    st.markdown(result["reply"])

    st.divider()

    # Metadata row
    m2, m3, m4 = st.columns(3)

    m2.metric("Needs Human Review", "Yes" if result["needs_review"] else "No")
    m3.metric("Language (RAG filter)", result["language"].capitalize())
    m4.metric("Tools Called", len(result["tools_called"]))

    st.divider()

    # KB Sources
    kb_sources = result.get("kb_sources", [])
    if kb_sources:
        st.subheader("📄 Knowledge Base Sources")
        st.caption("Documents consulted to generate this reply")
        for src in kb_sources:
            st.markdown(f"- **{src['file']}** — page {src['page']}")
    else:
        st.subheader("📄 Knowledge Base Sources")
        st.caption("No KB documents used — answer sourced entirely from Oracle AP data")

    # Tools detail (expandable)
    with st.expander("Tool calls audit log"):
        for i, t in enumerate(result["tools_called"], 1):
            st.markdown(f"**{i}. `{t['tool']}`**")
            st.json(t["args"])

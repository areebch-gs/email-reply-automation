from pipeline import process_email

tests = [
    # (email_body, mailbox, description)
    (
        "Hi, I submitted invoice 14000 back in December and it still hasn't been paid. Can you let me know the status and when I can expect payment? Thanks",
        "ukaccountspayable@sharkninja.com",
        "Invoice status — UK mailbox (English docs)",
    ),
    (
        "Hello, I need to make a change to one of my purchase orders but the system won't let me. How do I do this?",
        "ukaccountspayable@sharkninja.com",
        "PO change — UK mailbox (English docs only)",
    ),
    (
        "Hallo, ich kann meine Bestellung nicht ändern. Wie mache ich das?",
        "deaccountspayable@sharkninja.com",
        "PO change — DE mailbox (German docs only)",
    ),
    (
        "Hi, invoice 14000 still hasn't been paid. Can you tell me the status and also explain what your standard payment terms are and how I get paid?",
        "ukaccountspayable@sharkninja.com",
        "Invoice status + payment process — Oracle AND KB (English docs)",
    ),
]

for i, (email, mailbox, description) in enumerate(tests, 1):
    print(f"\n{'='*60}")
    print(f"TEST {i}: {description}")
    print(f"Mailbox : {mailbox}")
    print(f"Email   : {email}")
    print(f"\nPROCESSING...")

    result = process_email(email, mailbox=mailbox)

    print(f"\nREPLY:")
    print(result["reply"])
    print(f"\nLanguage     : {result['language']}")
    print(f"Confidence   : {result['confidence']}")
    print(f"Needs review : {result['needs_review']}")
    print(f"Tools called : {[t['tool'] for t in result['tools_called']]}")
    print(f"KB sources   : {result.get('kb_sources', [])}")

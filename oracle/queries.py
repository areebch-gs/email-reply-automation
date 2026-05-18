from oracle.client import OracleAPClient

# Fields we care about — keeps payloads small for the LLM
INVOICE_FIELDS = (
    "InvoiceId,InvoiceNumber,InvoiceAmount,InvoiceCurrency,InvoiceDate,"
    "Supplier,SupplierNumber,PaymentTerms,TermsDate,PaidStatus,AmountPaid,"
    "ValidationStatus,ApprovalStatus,AccountingStatus,PurchaseOrderNumber"
)

def search_invoices(
    client: OracleAPClient,
    invoice_number: str | None = None,
    supplier_name: str | None = None,
    supplier_number: str | None = None,
    limit: int = 5,
) -> list[dict]:
    """Search Oracle AP invoices by invoice number and/or supplier."""
    filters = []
    if invoice_number:
        filters.append(f'InvoiceNumber="{invoice_number}"')
    if supplier_number:
        filters.append(f'SupplierNumber="{supplier_number}"')
    elif supplier_name:
        # LIKE gives fuzzy match; Oracle REST uses % wildcard
        filters.append(f'Supplier LIKE "%{supplier_name}%"')

    params: dict = {
        "fields": INVOICE_FIELDS,
        "limit": limit,
        "orderBy": "InvoiceDate:desc",
    }
    if filters:
        params["q"] = ";".join(filters)

    data = client.get("invoices", params=params)
    return data.get("items", [])


def get_invoice_installments(client: OracleAPClient, invoice_id: int | str) -> list[dict]:
    """Fetch payment installments for an invoice — gives us DueDate and PaymentStatus."""
    data = client.get(f"invoices/{invoice_id}/child/invoiceInstallments")
    return data.get("items", [])


def build_invoice_context(invoice: dict, installments: list[dict]) -> str:
    """Format invoice + installments into a plain-text block for the LLM."""
    lines = [
        f"Invoice Number : {invoice.get('InvoiceNumber')}",
        f"Supplier       : {invoice.get('Supplier')}",
        f"Invoice Amount : {invoice.get('InvoiceAmount')} {invoice.get('InvoiceCurrency')}",
        f"Invoice Date   : {invoice.get('InvoiceDate')}",
        f"Payment Terms  : {invoice.get('PaymentTerms')}",
        f"Paid Status    : {invoice.get('PaidStatus')}",
        f"Amount Paid    : {invoice.get('AmountPaid')}",
        f"Validation     : {invoice.get('ValidationStatus')}",
        f"Approval       : {invoice.get('ApprovalStatus')}",
        f"PO Number      : {invoice.get('PurchaseOrderNumber') or 'N/A'}",
    ]

    if installments:
        lines.append("\nPayment Installments:")
        for inst in installments:
            lines.append(
                f"  Installment {inst.get('InstallmentNumber')}: "
                f"Due {inst.get('DueDate')} | "
                f"Amount {inst.get('GrossAmount')} | "
                f"Remaining {inst.get('AmountRemaining')} | "
                f"Status {inst.get('PaymentStatus')}"
            )

    return "\n".join(lines)

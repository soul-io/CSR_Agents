from airtable_logger import log_email_to_airtable
import os
import re
import time
from graph_helper import (
    get_folder_id,
    get_unread_emails,
    move_email,
    get_email_attachments
)

# --- Configuration ---
FOLDER_NEEDS_ATTENTION = "Needs Attention"
FOLDER_QUOTE_REQUESTS = "Quote Requests"
FOLDER_PURCHASE_ORDERS = "Purchase Orders"

PO_SUBJECT_BODY_KEYWORDS = ["purchase order", "po", r"p\.o\."]
PO_NUMBER_PATTERNS = [
    r"p[./]?o\s*(?:number|no\.?|#|num)?\s*:?-?\s*\d+",
    r"purchase order\s*(?:number|no\.?|#|num)?\s*:?-?\s*\d+",
    r"\b\d{6,10}\b"
]
PO_ATTACHMENT_NAME_KEYWORDS = ["po", "purchaseorder", "order", "purch"]
QUOTE_SUBJECT_BODY_KEYWORDS = [
    "quote", "request for quote", "rfq", "pricing", "lead time", "estimate", "ship time"
]
SPEC_SHEET_ATTACHMENT_KEYWORDS = ["spec", "specification", "datasheet", "drawing"]

def detect_purchase_order_signals(subject, body, attachments):
    score = 0
    subject = subject.lower()
    body = body.lower()
    filenames = [a['name'].lower() for a in attachments]

    if any(name.endswith(".pdf") for name in filenames):
        score += 1
    if "po#" in body or "purchase order" in body or len(re.findall(r"\bpo\s?[0-9]{4,10}\b", body)) > 0:
        score += 1
    if any("po" in name or re.search(r"\d{4,}", name) for name in filenames):
        score += 1

    return score >= 2

def categorize_email(email_data, attachments):
    subject_original = email_data.get('subject', '')
    subject_lower = subject_original.lower()

    body_content_data = email_data.get('body', {})
    body_content = body_content_data.get('content', '').lower() if body_content_data else ''
    if not body_content:
        body_content = email_data.get('bodyPreview', '').lower()

    has_attachments_flag = email_data.get('hasAttachments', False)
    content_to_search = subject_lower + " " + body_content

    is_po_pdf_present = False
    is_any_spec_sheet_present = False

    if has_attachments_flag and attachments:
        for att in attachments:
            att_name = att.get('name', '').lower()
            if any(spec in att_name for spec in SPEC_SHEET_ATTACHMENT_KEYWORDS):
                is_any_spec_sheet_present = True

    if has_attachments_flag and attachments:
        for att in attachments:
            att_name = att.get('name', '').lower()
            att_type = att.get('contentType', '').lower()
            if att_type == 'application/pdf' and any(kw in att_name for kw in PO_ATTACHMENT_NAME_KEYWORDS):
                is_po_pdf_present = True
                break

    if is_po_pdf_present:
        if not is_any_spec_sheet_present:
            for pattern in PO_NUMBER_PATTERNS:
                if re.search(pattern, content_to_search, re.IGNORECASE):
                    return FOLDER_PURCHASE_ORDERS
            for keyword in PO_SUBJECT_BODY_KEYWORDS:
                if re.search(rf"\b{re.escape(keyword)}\b", content_to_search, re.IGNORECASE):
                    return FOLDER_PURCHASE_ORDERS
            if subject_lower.startswith("fw:") or subject_lower.startswith("fwd:"):
                return FOLDER_PURCHASE_ORDERS
        else:
            print("Spec sheet present; skipping PO classification.")

    if detect_purchase_order_signals(subject_original, body_content, attachments):
        return FOLDER_PURCHASE_ORDERS

    if is_any_spec_sheet_present:
        return FOLDER_QUOTE_REQUESTS

    for keyword in QUOTE_SUBJECT_BODY_KEYWORDS:
        if re.search(rf"\b{re.escape(keyword)}\b", content_to_search, re.IGNORECASE):
            return FOLDER_QUOTE_REQUESTS

    return FOLDER_NEEDS_ATTENTION

# ✅ Wrapper function required for import
def process_emails():
    processed_email_summaries = []

    inbox_id = "inbox"  # You could refactor this if needed

    folder_ids = {
        FOLDER_NEEDS_ATTENTION: get_folder_id(FOLDER_NEEDS_ATTENTION, parent_folder_id=inbox_id),
        FOLDER_QUOTE_REQUESTS: get_folder_id(FOLDER_QUOTE_REQUESTS, parent_folder_id=inbox_id),
        FOLDER_PURCHASE_ORDERS: get_folder_id(FOLDER_PURCHASE_ORDERS, parent_folder_id=inbox_id)
    }

    if not all(folder_ids.values()):
        print("Exiting due to missing target folder(s).")
        return processed_email_summaries

    unread_emails = get_unread_emails(folder_id=inbox_id, top_n=20)

    if not unread_emails:
        print("No unread emails to process.")
        return processed_email_summaries

    for email in unread_emails:
        email_id = email.get('id')
        subject = email.get('subject', '')
        from_email = email.get('from', {}).get('emailAddress', {}).get('address', '')
        attachments = get_email_attachments(email_id) if email.get('hasAttachments') else []

        body = email.get('body', {}).get('content') or email.get('bodyPreview', '')

        category = categorize_email(email, attachments)

        log_email_to_airtable(
            email_id=email_id,
            from_email=from_email,
            email_subject=subject,
            email_content=body,
            email_attachments=attachments,
            attachments_names=[att.get('name', '') for att in attachments],
            attachments_types=[att.get('contentType', '') for att in attachments],
            po_detected=(category == FOLDER_PURCHASE_ORDERS),
            category=category,
            status="Sorted",
            reply_sent="No",
            notes=""
        )

        dest_folder_id = folder_ids.get(category)
        if dest_folder_id:
            print(f"Moving email ID {email_id} to '{category}'")
            move_email(email_id, dest_folder_id)
        else:
            print(f"No destination folder ID found for '{category}'")

        processed_email_summaries.append({
            "id": email_id,
            "subject": subject,
            "category": category
        })

    print("Email processing finished.")
    return processed_email_summaries


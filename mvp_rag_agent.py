import json

# Load test emails from local .json file
def load_test_emails(filepath="test_emails.json"):
    with open(filepath, "r") as f:
        return json.load(f)

# Very basic RAG-like classification
def classify_email(email_text):
    text = email_text.lower()
    if "purchase order" in text or "po-" in text:
        return "Purchase Orders"
    elif "quote" in text or "pricing" in text:
        return "Quote Requests"
    else:
        return "Needs Attention"

# Draft reply based on classification
def draft_reply(category, email_data):
    sender = email_data["from"]
    name = sender.split("@")[0].capitalize()

    if category == "Purchase Orders":
        subject = f"Re: {email_data['subject']}"
        body = f"""Dear {name},

Thank you for your Purchase Order. We have received it and will process it shortly. A formal order confirmation will follow.

Best regards,
The Clearline Team"""
    elif category == "Quote Requests":
        subject = f"Re: {email_data['subject']}"
        body = f"""Hi {name},

Thanks for your inquiry! We’re reviewing your quote request and will get back to you shortly with pricing and lead time.

Cheers,
The Clearline Team"""
    else:
        subject = f"Re: {email_data['subject']}"
        body = f"""Hello {name},

Thanks for reaching out. We’re reviewing your message and will get back to you shortly if action is needed.

Sincerely,
The Clearline Team"""

    return subject, body

# Logger
def log_output(email_id, category, subject, body):
    print("\n--- LOG ENTRY ---")
    print(f"Email ID: {email_id}")
    print(f"Category: {category}")
    print(f"Draft Subject: {subject}")
    print(f"Draft Body Preview: {body[:150]}...")

# MVP runner
def run_mvp():
    emails = load_test_emails()
    for email in emails:
        category = classify_email(email["body"])
        subject, body = draft_reply(category, email)
        log_output(email["id"], category, subject, body)

if __name__ == "__main__":
    run_mvp()

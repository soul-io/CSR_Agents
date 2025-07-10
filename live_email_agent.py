from graph_helper import get_unread_emails, move_email, get_email_attachments
from email_sorter import process_emails
from tools.email_tools import DraftAndLogEmailTool
from airtable_logger import log_email_to_airtable

def run_live_agent():
    print("📬 Checking for unread emails in shared inbox...")
    emails = get_unread_emails()

    if not emails:
        print("📭 No unread emails found.")
        return

    print(f"📨 {len(emails)} unread email(s) found.\n")

    for email in emails:
        print(f"--- Processing Email: {email['id']} | Subject: {email['subject']} ---")

        result = process_emails([email])[0]
        category = result['category']
        print(f"🧠 Classified as: {category}")

        draft_subject = result['draft_subject']
        draft_body = result['draft_body']

        # Send draft using tool
        draft_result = DraftAndLogEmailTool().run({
            "original_message_id": email['id'],
            "recipient_email": email['from']['emailAddress']['address'],
            "draft_subject": draft_subject,
            "draft_body": draft_body
        })

        # Log to Airtable
        log_email_to_airtable(
            message_id=email['id'],
            sender=email['from']['emailAddress']['address'],
            subject=email['subject'],
            category=category,
            draft_subject=draft_subject,
            draft_body=draft_body,
            status="Processed"
        )

        print(f"✅ Draft created and logged for: {email['id']}")
        print("---\n")

if __name__ == "__main__":
    run_live_agent()

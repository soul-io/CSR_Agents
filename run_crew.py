from dotenv import load_dotenv
import os
from graph_helper import get_unread_emails, get_email_attachments
from email_sorter import categorize_email
from crewai import Crew, Task, Process
from agents.basic_agents import emailer_agent, email_drafting_agent

# Load environment variables
load_dotenv()

print("🔧 Loaded environment configuration:")
print("SHARED_MAILBOX_ADDRESS:", os.getenv("SHARED_MAILBOX_ADDRESS"))
print("AIRTABLE_PERSONAL_TOKEN:", os.getenv("AIRTABLE_PERSONAL_TOKEN"))
print("AIRTABLE_BASE_ID:", os.getenv("AIRTABLE_BASE_ID"))
print("AIRTABLE_TABLE_NAME:", os.getenv("AIRTABLE_TABLE_NAME"))

# 🔍 STEP 1: Find a real Purchase Order email (or any email if needed)
def find_po_email_id():
    print("📥 Scanning inbox for a Purchase Order email...")
    emails = get_unread_emails(folder_id="inbox", top_n=20)
    for email in emails:
        attachments = get_email_attachments(email['id']) if email.get('hasAttachments') else []
        category = categorize_email(email, attachments)
        if category == "Purchase Orders":
            print(f"✅ Found PO email: {email['subject']} ({email['id']})")
            return email['id']
    print("⚠️ No Purchase Order email found.")
    return None

# 🧠 TASK 1: Email Sorting
email_sorting_task = Task(
    description=(
        "Sort unread Outlook emails from the shared inbox into one of the following folders: "
        "'Purchase Orders', 'Quote Requests', or 'Needs Attention'. "
        "Use your classification tool to analyze subject, body, and attachments. "
        "Log results to Airtable."
    ),
    agent=emailer_agent,
    expected_output="A summary showing how each email was categorized and logged."
)

# Set TEST_MODE manually or through your .env
TEST_MODE = os.getenv("TEST_MODE", "false").lower() == "true"

# Either find a real PO email or fallback to test ID
po_email_id = "test_id_po" if TEST_MODE else find_po_email_id()
if not po_email_id:
    print("❌ No PO email available to draft a reply for. Skipping drafting task.")
    tasks_to_run = [email_sorting_task]
else:
    # 🧠 TASK 2: PO Reply Drafting
    po_drafting_task = Task(
        description=f"""
You’ve been assigned to draft a reply for a real Purchase Order email.
Email ID: '{po_email_id}'

Instructions:
1. Use the 'Get Email Details Tool' to retrieve full content of email ID '{po_email_id}'.
2. Draft a polite reply confirming receipt of the PO and say an order confirmation is coming soon.
3. Use the 'Draft and Log Email Tool' to save and log your draft response.
        """,
        agent=email_drafting_agent,
        expected_output=(
            f"A drafted and logged email reply for PO ID '{po_email_id}' — include the "
            "recipient, reply subject, and a preview of the body."
        )
    )
    tasks_to_run = [email_sorting_task, po_drafting_task]

# 🚀 Launch the Crew
crew = Crew(
    agents=[emailer_agent, email_drafting_agent],
    tasks=tasks_to_run,
    verbose=True,
    process=Process.sequential
)

if __name__ == "__main__":
    print("🚀 Running live crew agent...")
    result = crew.kickoff()
    print("\n✅ Crew run complete.")
    print(result)



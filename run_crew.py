from dotenv import load_dotenv
import os
from graph_helper import get_unread_emails, get_email_attachments
from email_sorter import categorize_email # categorize_email is used by find_po_email_id
from crewai import Crew, Task, Process
from agents.basic_agents import emailer_agent, email_drafting_agent

# Load environment variables
load_dotenv()

print("🔧 Loaded environment configuration:")
print("SHARED_MAILBOX_ADDRESS:", os.getenv("SHARED_MAILBOX_ADDRESS"))
# print("AIRTABLE_PERSONAL_TOKEN:", os.getenv("AIRTABLE_PERSONAL_TOKEN")) # Potentially sensitive
# print("AIRTABLE_BASE_ID:", os.getenv("AIRTABLE_BASE_ID"))
# print("AIRTABLE_TABLE_NAME:", os.getenv("AIRTABLE_TABLE_NAME"))
print(f"TEST_MODE is: {os.getenv('TEST_MODE', 'false')}")


# 🔍 STEP 1: Find a real Purchase Order email (or any email if needed)
def find_po_email_id():
    """
    Scans unread emails for one categorized as "Purchase Orders".
    Returns the email ID if found, otherwise None.
    """
    print("📥 Scanning inbox for a Purchase Order email...")
    # Ensure SHARED_MAILBOX_ADDRESS is loaded for graph_helper functions
    if not os.getenv("SHARED_MAILBOX_ADDRESS"):
        print("CRITICAL: SHARED_MAILBOX_ADDRESS is not set. Cannot scan for emails.")
        return None
        
    emails = get_unread_emails(folder_id="inbox", top_n=20) # Check default inbox
    if not emails:
        print("No unread emails found in the inbox.")
        return None
        
    print(f"Found {len(emails)} unread emails to scan.")
    for email in emails:
        email_id_for_attachments = email.get('id')
        attachments = []
        if email_id_for_attachments and email.get('hasAttachments'):
            attachments = get_email_attachments(email_id_for_attachments)
        
        # Use the same categorize_email function from email_sorter
        category = categorize_email(email, attachments) 
        
        if category == "Purchase Orders": # Make sure "Purchase Orders" matches the constant in email_sorter
            print(f"✅ Found PO email: {email.get('subject', 'No Subject')} (ID: {email.get('id')})")
            return email.get('id')
            
    print("⚠️ No Purchase Order email found among unread emails.")
    return None

# 🧠 TASK 1: Email Sorting
# This task uses the EmailSorterTool which calls email_sorter.process_emails()
# process_emails() handles fetching, categorizing, logging (initial), and moving.
email_sorting_task = Task(
    description=(
        "Sort unread Outlook emails from the shared inbox into one of the following folders: "
        "'Purchase Orders', 'Quote Requests', or 'Needs Attention'. "
        "Use your classification tool (EmailSorterTool) to analyze subject, body, and attachments. "
        "The tool itself will log results to Airtable and move emails."
    ),
    agent=emailer_agent, # emailer_agent has EmailSorterTool
    expected_output="A summary string indicating the email sorting process was initiated and completed, including number of emails processed if available."
)

# Set TEST_MODE manually or through your .env
TEST_MODE = os.getenv("TEST_MODE", "false").lower() == "true"

po_email_id_for_drafting = None
if TEST_MODE:
    print("🧪 TEST_MODE is true. Using 'test_id_po' for drafting task.")
    po_email_id_for_drafting = "test_id_po"
else:
    print("⚙️ TEST_MODE is false. Attempting to find a real PO email for drafting task.")
    po_email_id_for_drafting = find_po_email_id()

tasks_to_run = [email_sorting_task] # Always run sorting task

if not po_email_id_for_drafting:
    print("❌ No PO email available (either not found or TEST_MODE was false and none identified). Skipping PO drafting task.")
else:
    print(f"📝 PO Email ID '{po_email_id_for_drafting}' will be used for the drafting task.")
    # 🧠 TASK 2: PO Reply Drafting
    po_drafting_task = Task(
        description=f"""
You’ve been assigned to draft a reply for a Purchase Order email.
The Email ID to use is: '{po_email_id_for_drafting}'

Instructions:
1. Use the 'Get Email Details Tool' to retrieve the full content (subject, body, sender) of email ID '{po_email_id_for_drafting}'.
2. Based on the retrieved details, draft a polite reply:
    - Acknowledge receipt of the Purchase Order.
    - State that an order confirmation will be sent soon.
    - Keep the tone professional and courteous.
3. Use the 'Draft and Log Email Tool' to save and log your drafted response. Ensure you use the correct recipient email from the original email's details.
        """,
        agent=email_drafting_agent, # email_drafting_agent has GetEmailDetailsTool and DraftAndLogEmailTool
        expected_output=(
            f"A JSON string detailing the drafted and logged email reply for PO ID '{po_email_id_for_drafting}'. "
            "This should include the recipient, reply subject, and a preview of the body, plus confirmation of logging."
        )
    )
    tasks_to_run.append(po_drafting_task)

# 🚀 Launch the Crew
crew = Crew(
    agents=[emailer_agent, email_drafting_agent],
    tasks=tasks_to_run,
    verbose=True, # Set to 2 or True for detailed crew output
    process=Process.sequential
)

if __name__ == "__main__":
    print("🚀 Running Crew...")
    # Kickoff the crew's work
    result = crew.kickoff()
    
    print("\n✅ Crew run complete.")
    print("📋 Final Result from Crew Kickoff:")
    print(result)


if __name__ == "__main__":
    print("🚀 Running live crew agent...")
    result = crew.kickoff()
    print("\n✅ Crew run complete.")
    print(result)



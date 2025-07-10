from graph_helper import get_unread_emails # Only need this if we were to check before calling, but process_emails does it
from email_sorter import process_emails # process_emails will handle fetching and all logic
# from email_tools import DraftAndLogEmailTool # No longer used in this simplified version
# from airtable_logger import log_email_to_airtable # process_emails calls airtable_logger directly

def run_live_agent():
    print("📬 Triggering batch email processing via email_sorter.process_emails()...")
    
    # Call process_emails from email_sorter.py once. 
    # This function handles fetching, categorizing, logging, and moving emails in batch.
    results = process_emails() 

    if results is None: 
        print("⚠️ email_sorter.process_emails() did not return results or exited early (e.g., critical folder missing).")
    elif not results: 
        print("📭 No unread emails were processed by email_sorter.process_emails(), or no emails were found initially.")
    else:
        # Assuming process_emails now returns a list of processed item summaries (which the refactor aimed for)
        # If the refactor of email_sorter.py failed, this part might not be accurate.
        # For now, let's assume it might return a list if successful.
        print(f"✅ email_sorter.process_emails() reported processing for {len(results)} email(s).")
        # for result in results:
        #     print(f"  - Processed Email ID: {result.get('id')}, Category: {result.get('category')}")

    print("\n--- Live agent trigger run complete ---")

if __name__ == "__main__":
    run_live_agent()

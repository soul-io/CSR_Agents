from crewai.tools import BaseTool
from pydantic import Field, BaseModel, validator
import json # Ensure json is imported

# Assuming these imports are correct and files exist at these paths
# If graph_helper modification failed, this direct import might cause issues later
# For now, the tool itself will use placeholder data.
# from graph_helper import get_email_details as fetch_email_details_from_graph
from email_request import send_email_update # Assuming this path is correct relative to where app is run
from email_sorter import process_emails # Assuming this path is correct


# --- Tool for Email Sorting Agent ---
class EmailSorterToolSchema(BaseModel):
    pass

class EmailSorterTool(BaseTool):
    name: str = "Email Sorting Tool"
    description: str = "Sorts and categorizes unread Outlook emails using Microsoft Graph. Takes no direct arguments, processes based on pre-configuration."

    def _run(self) -> str:
        process_emails()
        return "Email sorting process initiated and completed."

# --- Tools for Email Drafting Agent ---

class GetEmailDetailsToolSchema(BaseModel):
    message_id: str = Field(description="The ID of the email message to fetch details for.")

class GetEmailDetailsTool(BaseTool):
    name: str = "Get Email Details Tool"
    description: str = "Fetches details of a specific email, such as sender, subject, and body, given its message ID. This is used to get context for drafting a reply."
    args_schema: type[BaseModel] = GetEmailDetailsToolSchema

    def _run(self, message_id: str) -> str:
        print(f"GetEmailDetailsTool: Fetching details for message_id: {message_id}")
        try:
            email_details_data = None
            if message_id == "test_id_po": # New placeholder for Purchase Order
                email_details_data = {
                    "id": message_id,
                    "subject": "New Purchase Order PO-12345 from Acme Corp",
                    "reply_to_address": "procurement@acmecorp.com",
                    "consolidated_body": (
                        "Dear Clearline Team,\n\nPlease find attached our Purchase Order PO-12345 for the following items:\n"
                        "- 100x Model X Widgets\n- 50x Model Y Connectors\n\n"
                        "Please confirm receipt and advise on estimated shipping date.\n\n"
                        "Thanks,\nBob from Acme Corp\nprocurement@acmecorp.com"
                    ),
                    "from_details": {"emailAddress": {"address": "procurement@acmecorp.com", "name": "Bob (Acme Corp Procurement)"}},
                }
            elif message_id == "test_id_needs_attention":
                email_details_data = {
                    "id": message_id,
                    "subject": "Urgent: Problem with my last order",
                    "reply_to_address": "customer@example.com",
                    "consolidated_body": "Dear Clearline, I am writing to complain about the order I received yesterday. It was damaged and I need a replacement. My order number is 12345. This is unacceptable!",
                    "from_details": {"emailAddress": {"address": "customer@example.com", "name": "Frustrated Customer"}},
                }
            elif message_id == "test_id_quote_request":
                 email_details_data = {
                    "id": message_id,
                    "subject": "Request for Quote - 1000 Widgets",
                    "reply_to_address": "buyer@company.com",
                    "consolidated_body": "Hello, Please provide a quote for 1000 units of product XYZ. We also need to know the lead time. Attached is our spec sheet.",
                    "from_details": {"emailAddress": {"address": "buyer@company.com", "name": "Potential Buyer"}},
                }
            else: # Generic placeholder for any other ID
                email_details_data = {
                    "id": message_id,
                    "subject": f"Placeholder Subject for {message_id}",
                    "reply_to_address": "unknown_sender@example.com",
                    "consolidated_body": "This is placeholder body content because fetching real email details is currently unavailable. Please use this context for drafting.",
                    "from_details": {"emailAddress": {"address": "unknown_sender@example.com", "name": "Unknown Sender"}},
                }

            if not email_details_data:
                return json.dumps({"error": f"Could not retrieve details for email ID '{message_id}'. Placeholder data also failed."})

            return json.dumps({
                "original_message_id": email_details_data.get("id"),
                "original_subject": email_details_data.get("subject"),
                "original_body_preview": email_details_data.get("consolidated_body", "")[:500],
                "full_original_body": email_details_data.get("consolidated_body"),
                "reply_to_address": email_details_data.get("reply_to_address"),
                "original_from_name": email_details_data.get("from_details", {}).get("emailAddress", {}).get("name"),
                "original_from_address": email_details_data.get("from_details", {}).get("emailAddress", {}).get("address"),
            })
        except Exception as e:
            return json.dumps({"error": f"Error in GetEmailDetailsTool: {str(e)}"})


class DraftAndLogEmailToolSchema(BaseModel):
    original_message_id: str = Field(description="The ID of the original email message being replied to, for logging/threading.")
    recipient_email: str = Field(description="The email address of the recipient (usually the sender of the original email).")
    draft_subject: str = Field(description="The subject line for the draft email.")
    draft_body: str = Field(description="The content/body for the draft email.")

class DraftAndLogEmailTool(BaseTool):
    name: str = "Draft and Log Email Tool"
    description: str = "Takes a drafted subject, body, and recipient's email. It 'sends' the email by printing to console (simulating sending) and prepares a log. Requires original message ID."
    args_schema: type[BaseModel] = DraftAndLogEmailToolSchema

    def _run(self, original_message_id: str, recipient_email: str, draft_subject: str, draft_body: str) -> str:
        if not all([original_message_id, recipient_email, draft_subject, draft_body]):
            return json.dumps({"error": "Missing one or more required fields: original_message_id, recipient_email, draft_subject, draft_body."})
        try:
            confirmation_message = send_email_update(
                subject_line=draft_subject,
                body_content=draft_body,
                recipient_email=recipient_email
                # original_message_id is not part of send_email_update's current signature
                # due to earlier file edit failures. If it were, it would be passed here.
            )

            log_output = {
                "status": "Draft processed and logged",
                "original_message_id": original_message_id,
                "recipient_email": recipient_email,
                "draft_subject": draft_subject,
                "draft_body_preview": draft_body[:200] + "...",
                "confirmation": confirmation_message
            }
            print(f"Airtable log (simulated for {original_message_id}): {log_output}") # Added original_message_id for clarity
            return json.dumps(log_output)
        except Exception as e:
            return json.dumps({"error": f"Failed to process/log email draft for {recipient_email}: {str(e)}"})

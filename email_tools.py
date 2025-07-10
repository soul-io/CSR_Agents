from crewai.tools import BaseTool
from pydantic import Field, BaseModel, validator
import json
# Import the real function from graph_helper
from graph_helper import get_email_details as fetch_real_email_details
from email_request import send_email_update
from email_sorter import process_emails # This is used by EmailSorterTool


# --- Tool for Email Sorting Agent ---
class EmailSorterToolSchema(BaseModel):
    pass

class EmailSorterTool(BaseTool):
    name: str = "Email Sorting Tool"
    description: str = "Sorts and categorizes unread Outlook emails using Microsoft Graph. Takes no direct arguments, processes based on pre-configuration."

    def _run(self) -> str:
        # Assuming process_emails() is the batch processor from email_sorter
        # and it returns a list of processed email summaries or an empty list/None.
        results = process_emails()
        if results is None:
            return "Email sorting process initiated but encountered an issue (e.g., folder setup)."
        elif not results:
            return "Email sorting process initiated and completed. No unread emails found or processed."
        else:
            return f"Email sorting process initiated and completed. {len(results)} email(s) were processed."

# --- Tools for Email Drafting Agent ---

class GetEmailDetailsToolSchema(BaseModel):
    message_id: str = Field(description="The ID of the email message to fetch details for.")

class GetEmailDetailsTool(BaseTool):
    name: str = "Get Email Details Tool"
    description: str = "Fetches details of a specific email, such as sender, subject, and body, given its message ID. This is used to get context for drafting a reply."
    args_schema: type[BaseModel] = GetEmailDetailsToolSchema

    def _run(self, message_id: str) -> str:
        print(f"GetEmailDetailsTool: Fetching REAL details for message_id: {message_id}")
        try:
            # Use the real function from graph_helper
            email_details_data = fetch_real_email_details(message_id=message_id)

            if not email_details_data:
                # Handle case where graph_helper returns None (e.g., email not found or API error)
                error_message = f"Could not retrieve details for email ID '{message_id}'. The email might not exist or an API error occurred."
                print(f"GetEmailDetailsTool: {error_message}")
                return json.dumps({"error": error_message})

            # Map the data from graph_helper.get_email_details to the expected output structure
            # graph_helper returns: id, subject, consolidated_body, reply_to_address, from_name, from_address, etc.
            # Tool expected output: original_message_id, original_subject, full_original_body, reply_to_address, original_from_name, original_from_address
            
            output_data = {
                "original_message_id": email_details_data.get("id"),
                "original_subject": email_details_data.get("subject"),
                "full_original_body": email_details_data.get("consolidated_body"),
                "reply_to_address": email_details_data.get("reply_to_address"),
                "original_from_name": email_details_data.get("from_name"),
                "original_from_address": email_details_data.get("from_address") 
                # body_preview can be generated if needed: email_details_data.get("consolidated_body", "")[:500]
            }
            
            print(f"GetEmailDetailsTool: Successfully fetched and mapped details for {message_id}")
            return json.dumps(output_data)
            
        except Exception as e:
            error_str = f"Error in GetEmailDetailsTool while processing message ID '{message_id}': {str(e)}"
            print(f"GetEmailDetailsTool: {error_str}")
            # It's good practice to include the original message_id in the error if possible
            return json.dumps({"error": error_str, "message_id": message_id})


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
        
        print(f"DraftAndLogEmailTool: Simulating sending email to: {recipient_email}, Subject: {draft_subject}")
        try:
            # Simulate sending email
            confirmation_message = send_email_update(
                subject_line=draft_subject,
                body_content=draft_body,
                recipient_email=recipient_email
            )

            # Log output (simulates what might go to Airtable or another logging system)
            log_output = {
                "status": "Draft processed and logged (simulated)",
                "original_message_id": original_message_id,
                "recipient_email": recipient_email,
                "draft_subject": draft_subject,
                "draft_body_preview": draft_body[:200] + "...", # Preview of the body
                "confirmation_from_send_email_update": confirmation_message 
            }
            print(f"DraftAndLogEmailTool: Logging (simulated): {log_output}")
            return json.dumps(log_output)
        except Exception as e:
            error_str = f"Failed to process/log email draft for {recipient_email} (Original ID: {original_message_id}): {str(e)}"
            print(f"DraftAndLogEmailTool: {error_str}")
            return json.dumps({"error": error_str})


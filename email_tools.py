from crewai.tools import BaseTool
from pydantic import Field, BaseModel
import json

# Imports
from graph_helper import get_email_details as fetch_real_email_details
from email_request import send_email_update
from email_sorter import process_emails  # This must be defined in email_sorter.py


# --- Email Sorting Tool ---

class EmailSorterToolSchema(BaseModel):
    pass  # No args needed


class EmailSorterTool(BaseTool):
    name: str = "Email Sorting Tool"
    description: str = "Sorts and categorizes unread Outlook emails using Microsoft Graph. No arguments required."
    args_schema: type[BaseModel] = EmailSorterToolSchema

    def _run(self) -> str:
        print(f"[{self.name}] Starting tool execution.")
        results = process_emails()
        if results is None:
            return "❌ Email sorting failed due to a critical setup error."
        elif not results:
            return "✅ Email sorting complete. No unread emails found."
        else:
            print(f"[{self.name}] Processed {len(results)} emails.")
            return f"✅ Email sorting complete. Processed {len(results)} emails."


# --- Get Email Details Tool ---

class GetEmailDetailsToolSchema(BaseModel):
    message_id: str = Field(description="The ID of the email message to fetch details for.")


class GetEmailDetailsTool(BaseTool):
    name: str = "Get Email Details Tool"
    description: str = "Fetches sender, subject, body, and metadata for a given email message ID."
    args_schema: type[BaseModel] = GetEmailDetailsToolSchema

    def _run(self, message_id: str) -> str:
        print(f"[{self.name}] Fetching email details for ID: {message_id}")
        try:
            email_details_data = fetch_real_email_details(message_id=message_id)

            if not email_details_data:
                error_message = f"Could not retrieve email ID '{message_id}'. It may not exist or an API error occurred."
                print(f"[{self.name}] {error_message}")
                return json.dumps({"error": error_message})

            output_data = {
                "original_message_id": email_details_data.get("id"),
                "original_subject": email_details_data.get("subject"),
                "full_original_body": email_details_data.get("consolidated_body"),
                "reply_to_address": email_details_data.get("reply_to_address"),
                "original_from_name": email_details_data.get("from_name"),
                "original_from_address": email_details_data.get("from_address")
            }

            print(f"[{self.name}] Success. Returning email details.")
            return json.dumps(output_data)

        except Exception as e:
            error_str = f"Error in {self.name}: {str(e)}"
            print(f"[{self.name}] {error_str}")
            return json.dumps({"error": error_str, "message_id": message_id})


# --- Draft and Log Email Tool ---

class DraftAndLogEmailToolSchema(BaseModel):
    original_message_id: str = Field(description="ID of the original email being replied to.")
    recipient_email: str = Field(description="Email address of the recipient.")
    draft_subject: str = Field(description="Subject line for the draft email.")
    draft_body: str = Field(description="Body content for the draft email.")


class DraftAndLogEmailTool(BaseTool):
    name: str = "Draft and Log Email Tool"
    description: str = "Simulates sending a drafted email and logs the draft output."
    args_schema: type[BaseModel] = DraftAndLogEmailToolSchema

    def _run(self, original_message_id: str, recipient_email: str, draft_subject: str, draft_body: str) -> str:
        print(f"[{self.name}] Preparing to send draft to {recipient_email} with subject: {draft_subject}")
        try:
            if not all([original_message_id, recipient_email, draft_subject, draft_body]):
                return json.dumps({
                    "error": "Missing required fields: original_message_id, recipient_email, draft_subject, draft_body."
                })

            confirmation_message = send_email_update(
                subject_line=draft_subject,
                body_content=draft_body,
                recipient_email=recipient_email
            )

            log_output = {
                "status": "✅ Draft processed and logged (simulated)",
                "original_message_id": original_message_id,
                "recipient_email": recipient_email,
                "draft_subject": draft_subject,
                "draft_body_preview": draft_body[:200] + "...",
                "confirmation_from_send_email_update": confirmation_message
            }

            print(f"[{self.name}] Success. Logging output.")
            return json.dumps(log_output)

        except Exception as e:
            error_str = f"Failed to process/log draft email: {str(e)}"
            print(f"[{self.name}] {error_str}")
            return json.dumps({"error": error_str})


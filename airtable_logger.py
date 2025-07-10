from airtable import Airtable
import os
from dotenv import load_dotenv

# Ensure environment variables are loaded at the start of this module
load_dotenv()

# Airtable credentials and table config
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_TABLE_NAME = "CSR_Log" # This is a string, so it's fine
AIRTABLE_TOKEN = os.getenv("AIRTABLE_PERSONAL_TOKEN")

# Initialize Airtable client
# This will likely still fail if the .env file is missing or keys are not set,
# but the load_dotenv() call is in the right place now.
airtable_client_initialized = False
airtable = None
if AIRTABLE_BASE_ID and AIRTABLE_TABLE_NAME and AIRTABLE_TOKEN:
    try:
        airtable = Airtable(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME, api_key=AIRTABLE_TOKEN)
        airtable_client_initialized = True
        print("Airtable client initialized successfully.")
    except Exception as e:
        print(f"⚠️ Failed to initialize Airtable client: {e}. Logging to Airtable will be skipped.")
else:
    print("⚠️ Airtable credentials (AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME, AIRTABLE_PERSONAL_TOKEN) not found in environment. Logging to Airtable will be skipped.")


def log_email_to_airtable(
    email_id,
    from_email,
    email_subject,
    email_content,
    email_attachments,
    attachments_names,
    attachments_types,
    po_detected,
    category,
    status,
    reply_sent,
    notes
):
    if not airtable_client_initialized or not airtable:
        print(f"ℹ️ Skipping Airtable log for email: {email_subject} (Airtable client not initialized).")
        return

    try:
        fields = {
            "Email_ID": email_id,
            "From_Email": from_email,
            "Email_Subject": email_subject,
            "Email_Content": email_content, # Consider truncating if very long
            "Email_Attachments": str(email_attachments), # Could be too long, consider summarizing
            "Attachments_Names": attachments_names, # This is a list, Airtable might prefer a string
            "Attachments_Types": attachments_types, # This is a list, Airtable might prefer a string
            "PO_Detected": po_detected,
            "Category": category,
            "Status": status,
            "Reply_Sent": reply_sent,
            "Notes": notes
        }

        # Convert lists to comma-separated strings if Airtable field is not multi-select/linked record
        if isinstance(fields["Attachments_Names"], list):
            fields["Attachments_Names"] = ", ".join(fields["Attachments_Names"])
        if isinstance(fields["Attachments_Types"], list):
            fields["Attachments_Types"] = ", ".join(fields["Attachments_Types"])
        if len(fields["Email_Content"]) > 1000: # Example truncation
            fields["Email_Content"] = fields["Email_Content"][:997] + "..."
        if len(fields["Email_Attachments"]) > 1000:
            fields["Email_Attachments"] = fields["Email_Attachments"][:997] + "..."


        airtable.insert(fields)
        print(f"✅ Logged email to Airtable: {email_subject}")
    except Exception as e:
        print(f"❌ Failed to log email to Airtable for subject '{email_subject}': {e}")

from airtable import Airtable
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Airtable credentials and config
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_TABLE_NAME = os.getenv("AIRTABLE_TABLE_NAME")
AIRTABLE_TOKEN = os.getenv("AIRTABLE_PERSONAL_TOKEN")

# Initialize Airtable client
airtable_client_initialized = False
airtable = None
if AIRTABLE_BASE_ID and AIRTABLE_TABLE_NAME and AIRTABLE_TOKEN:
    try:
        airtable = Airtable(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME, api_key=AIRTABLE_TOKEN)
        airtable_client_initialized = True
        print("✅ Airtable client initialized successfully.")
    except Exception as e:
        print(f"⚠️ Failed to initialize Airtable client: {e}. Logging to Airtable will be skipped.")
else:
    print("⚠️ Airtable credentials not found in environment. Logging to Airtable will be skipped.")

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
        # Sanitize and truncate fields
        def safe_str(val, max_len=1000):
            return str(val)[:max_len-3] + "..." if len(str(val)) > max_len else str(val)

        fields = {
            "Email_ID": safe_str(email_id),
            "From_Email": safe_str(from_email),
            "Email_Subject": safe_str(email_subject),
            "Email_Content": safe_str(email_content),  # ← this comma was missing
            "Email_Attachments": safe_str(
                [att["filename"] for att in email_attachments]
            ) if isinstance(email_attachments, list) else safe_str(email_attachments),
            "Attachments_Names": ", ".join(map(str, attachments_names)) if isinstance(attachments_names, list) else safe_str(attachments_names),
            "Attachments_Types": ", ".join(map(str, attachments_types)) if isinstance(attachments_types, list) else safe_str(attachments_types),
            "PO_Detected": bool(po_detected),
            "Category": safe_str(category),
            "Status": safe_str(status),
            "Reply_Sent": bool(reply_sent),
            "Notes": safe_str(notes)
        }

        print("📤 Final fields being sent to Airtable:")
        for key, value in fields.items():
            print(f"  {key}: {type(value)} → {str(value)[:100]}")

        airtable.insert(fields)
        print(f"✅ Logged email to Airtable: {email_subject}")

    except Exception as e:
        print(f"❌ Failed to log email to Airtable for subject '{email_subject}': {e}")

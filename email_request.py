import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def send_email_update(subject_line, body_content, recipient_email):
    """Sends an email update with the specified subject and content.

    Args:
        subject_line (str): The subject of the email.
        body_content (str): The content of the email.
        recipient_email (str): The email address of the recipient.

    Returns:
        str: Confirmation message indicating whether the email was sent successfully or not.
    """
    # This function would ideally interact with an email sending service (e.g., Gmail API, SendGrid)
    # For demonstration purposes, we'll just print the email details here.
    print(f"Sending email to: {recipient_email}")
    print(f"Subject: {subject_line}")
    print(f"Body:\n{body_content}")
    return "Email sent successfully!"

# Example usage (you can replace this with your actual logic)
if __name__ == "__main__":
    subject = "Test Email"
    body = "This is a test email."
    recipient = "test@example.com"

    result = send_email_update(subject, body, recipient)
    print(result)
import os
import msal
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
TENANT_ID = os.getenv("TENANT_ID")

# Critical check for environment variables - Restored to original behavior
if not CLIENT_ID or not CLIENT_SECRET or not TENANT_ID:
    missing_vars_list = []
    if not CLIENT_ID:
        missing_vars_list.append("CLIENT_ID")
    if not CLIENT_SECRET:
        missing_vars_list.append("CLIENT_SECRET")
    if not TENANT_ID:
        missing_vars_list.append("TENANT_ID")

    error_message_vars = f"CRITICAL ERROR: The following environment variables are missing: {', '.join(missing_vars_list)}."
    print(error_message_vars)
    print("Please check your .env file and ensure it's in the same directory as auth.py.")
    print("Ensure the .env file is formatted correctly (e.g., VARIABLE=\"value\").")
    exit() # Original behavior: exit if credentials are not found

# AUTHORITY and SCOPES should be defined only if CLIENT_ID etc., are present.
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
SCOPES = ["https://graph.microsoft.com/.default"] # Default scope for client credentials flow

def get_access_token():
    # app object creation and token acquisition should only happen if creds were found.
    # The check at the module level handles the exit if they are not.
    app = msal.ConfidentialClientApplication(
        CLIENT_ID,
        authority=AUTHORITY,
        client_credential=CLIENT_SECRET
    )

    result = app.acquire_token_silent(SCOPES, account=None)

    if not result:
        print("No token in cache, acquiring new one for client...")
        result = app.acquire_token_for_client(scopes=SCOPES)

    if "access_token" in result:
        # print("Successfully acquired access token.") # Optional: for verbose logging
        return result["access_token"]
    else:
        # Construct detailed error message
        error_message = "Could not acquire access token. Error details:\n"
        error_message += f"  Error: {result.get('error')}\n"
        error_message += f"  Error Description: {result.get('error_description')}\n"
        error_message += f"  Correlation ID: {result.get('correlation_id')}\n"
        error_message += "  Troubleshooting suggestions:\n"
        error_message += "  1. Double-check CLIENT_ID, CLIENT_SECRET, and TENANT_ID in your .env file.\n"
        error_message += "  2. Ensure the Client Secret is the 'Value' (not the 'Secret ID') from Azure portal.\n"
        error_message += "  3. Verify that the application has 'Mail.ReadWrite' (Application type) permissions granted and admin consented in Azure AD for the specified scopes.\n"
        error_message += "  4. Check if the App Registration is enabled in Azure.\n"
        error_message += "  5. Ensure the .env file is correctly formatted and loaded."
        # Instead of just printing, raise an exception to signal failure more strongly.
        # Callers can then handle this exception if needed.
        raise Exception(error_message)

if __name__ == "__main__":
    try:
        print("Attempting to acquire access token (auth.py direct test)...")
        token = get_access_token()
        print(f"Successfully acquired access token (first 20 chars): {token[:20]}...")
    except Exception as e:
        # This will catch the exception raised by get_access_token on failure
        print(f"Failed to acquire access token in auth.py direct test: {e}")

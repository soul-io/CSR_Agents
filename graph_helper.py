import os
import requests
import json
from auth import get_access_token  # To get the token from our auth.py
from dotenv import load_dotenv

load_dotenv()  # ✅ This tells Python to load variables from .env

GRAPH_API_ENDPOINT = "https://graph.microsoft.com/v1.0"
SHARED_MAILBOX_ADDRESS = os.getenv("SHARED_MAILBOX_ADDRESS")  # ✅ Fixed

if not SHARED_MAILBOX_ADDRESS:
    print("CRITICAL ERROR: SHARED_MAILBOX_ADDRESS is not set in your .env file.")
    print('Please add SHARED_MAILBOX_ADDRESS="your_shared_mailbox@example.com" to .env')
    exit()


def make_graph_api_call(method, url_suffix, data=None, params=None, extra_headers=None):
    """Helper function to make calls to Microsoft Graph API."""
    token = get_access_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    if extra_headers:
        headers.update(extra_headers)

    full_url = f"{GRAPH_API_ENDPOINT}{url_suffix}"
    # print(f"DEBUG: Calling Graph API: {method} {full_url} Params: {params} Data: {data}") # Optional debug

    try:
        if method.upper() == "GET":
            response = requests.get(full_url, headers=headers, params=params)
        elif method.upper() == "POST":
            response = requests.post(full_url, headers=headers, json=data, params=params)
        elif method.upper() == "PATCH":
            response = requests.patch(full_url, headers=headers, json=data, params=params)
        elif method.upper() == "DELETE":
            response = requests.delete(full_url, headers=headers, params=params)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

        # print(f"DEBUG: Response Status: {response.status_code}") # Optional debug
        # if response.content:
        #     try:
        #         print(f"DEBUG: Response JSON: {response.json()}") # Optional debug
        #     except json.JSONDecodeError:
        #         print(f"DEBUG: Response Text: {response.text}") # Optional debug

        response.raise_for_status() 
        if response.status_code == 204: # No Content
            return None
        if response.content:
             return response.json()
        return None 
    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error calling Graph API: {e.response.status_code} {e.response.reason}")
        try:
            print(f"Error details: {e.response.json()}")
        except json.JSONDecodeError:
            print(f"Error details (non-JSON): {e.response.text}")
        raise
    except Exception as e:
        print(f"Error calling Graph API endpoint {url_suffix}: {e}")
        raise

def get_folder_id(folder_name, parent_folder_id=None):
    """
    Gets the ID of a folder.
    If parent_folder_id is provided, searches within that folder.
    Otherwise, searches at the root of the shared mailbox.
    Case-sensitive for folder_name.
    """
    print(f"Attempting to get ID for folder: '{folder_name}' in mailbox '{SHARED_MAILBOX_ADDRESS}'")
    if parent_folder_id:
        print(f"Searching within parent folder ID: {parent_folder_id}")
        url_suffix = f"/users/{SHARED_MAILBOX_ADDRESS}/mailFolders/{parent_folder_id}/childFolders"
    else:
        print("Searching at mailbox root.")
        url_suffix = f"/users/{SHARED_MAILBOX_ADDRESS}/mailFolders"
    
    params = {"$filter": f"displayName eq '{folder_name}'", "$select": "id,displayName"}
    
    try:
        response = make_graph_api_call("GET", url_suffix, params=params)
        if response and response.get("value"):
            if len(response["value"]) == 1:
                folder_id = response["value"][0]["id"]
                print(f"Found folder '{folder_name}' with ID: {folder_id}")
                return folder_id
            elif len(response["value"]) > 1:
                print(f"Warning: Multiple folders found with the name '{folder_name}' under the specified parent. Using the first one.")
                folder_id = response["value"][0]["id"]
                print(f"Using ID: {folder_id} for folder '{folder_name}'")
                return folder_id
            else:
                search_location = f"under parent ID {parent_folder_id}" if parent_folder_id else "at mailbox root"
                print(f"Folder '{folder_name}' not found {search_location} in mailbox '{SHARED_MAILBOX_ADDRESS}'.")
                return None
        else:
            search_location = f"under parent ID {parent_folder_id}" if parent_folder_id else "at mailbox root"
            print(f"No 'value' in response or empty response when searching for folder '{folder_name}' {search_location}. Response: {response}")
            return None
    except Exception as e:
        # Catching exception here so one folder failing doesn't stop everything if called in a loop
        print(f"Error getting folder ID for '{folder_name}': {e}")
        return None

def get_unread_emails(folder_id="inbox", top_n=10):
    """Gets the top N unread emails from a specified folder (default is inbox)."""
    folder_to_query = folder_id 
    if folder_id.lower() == "inbox":
         print(f"Fetching unread emails from Inbox of {SHARED_MAILBOX_ADDRESS}...")
         url_suffix = f"/users/{SHARED_MAILBOX_ADDRESS}/mailFolders/inbox/messages"
    else:
        print(f"Fetching unread emails from folder ID {folder_id} of {SHARED_MAILBOX_ADDRESS}...")
        url_suffix = f"/users/{SHARED_MAILBOX_ADDRESS}/mailFolders/{folder_id}/messages"

    params = {
        "$filter": "isRead eq false",
        "$top": top_n,
        "$select": "id,subject,sender,receivedDateTime,body,bodyPreview,hasAttachments", # body is included
        "$orderby": "receivedDateTime desc"
    }
    try:
        response = make_graph_api_call("GET", url_suffix, params=params)
        if response and "value" in response:
            print(f"Found {len(response['value'])} unread emails.")
            return response["value"]
        print("No unread emails found or error in response.")
        return []
    except Exception as e:
        print(f"Error fetching unread emails: {e}")
        return []

def get_email_attachments(message_id):
    """Fetches attachment details for a specific email, excluding inline attachments."""
    print(f"  Fetching attachments for message ID {message_id}...")
    url_suffix = f"/users/{SHARED_MAILBOX_ADDRESS}/messages/{message_id}/attachments"
    params = {"$select": "id,name,contentType,size,isInline"} 
    try:
        response = make_graph_api_call("GET", url_suffix, params=params)
        if response and "value" in response:
            attachments = [att for att in response["value"] if not att.get("isInline", False)]
            print(f"    Found {len(attachments)} non-inline attachments.")
            return attachments 
        print(f"    No attachments found for message ID {message_id} or error in response.")
        return []
    except Exception as e:
        print(f"    Error fetching attachments for message ID {message_id}: {e}")
        return []

def move_email(message_id, destination_folder_id):
    """Moves an email to a specified destination folder."""
    print(f"Moving message ID {message_id} to folder ID {destination_folder_id} in mailbox {SHARED_MAILBOX_ADDRESS}...")
    url_suffix = f"/users/{SHARED_MAILBOX_ADDRESS}/messages/{message_id}/move"
    payload = {
        "destinationId": destination_folder_id
    }
    try:
        moved_message = make_graph_api_call("POST", url_suffix, data=payload)
        # A successful move might return the moved item (201) or just a 200 OK with no body depending on exact API version/behavior for moves.
        # Graph API often returns the moved item.
        if moved_message and moved_message.get("id"):
             print(f"Successfully moved message ID {message_id} to folder ID {destination_folder_id}.")
             return moved_message 
        # If no specific moved_message content but no error, assume success (e.g. 204 No Content is handled by make_graph_api_call returning None)
        # However, 'move' usually returns the item. This part might need adjustment based on observed behavior if 'None' is returned on success.
        print(f"Message ID {message_id} move action completed. Response: {moved_message}")
        return moved_message # Return whatever response we got, could be None for 204 or the item for 201

    except Exception as e:
        print(f"Error moving message ID {message_id}: {e}")
        return None
def get_email_details(message_id: str) -> dict | None:
    """
    Fetches specific details for a single email message to provide context for drafting a reply.
    Includes subject, body (consolidated), and sender information (reply_to_address).
    """
    print(f"Fetching full details for message ID {message_id} in mailbox {SHARED_MAILBOX_ADDRESS}...")
    
    # Define the fields you want to select.
    # 'from' gives the original sender. 'sender' is who sent it if on behalf of someone.
    # 'body' is preferred, 'bodyPreview' is a fallback.
    select_fields = "id,subject,body,bodyPreview,from,sender,toRecipients,ccRecipients,conversationId"
    url_suffix = f"/users/{SHARED_MAILBOX_ADDRESS}/messages/{message_id}"
    params = {"$select": select_fields}

    try:
        response_data = make_graph_api_call("GET", url_suffix, params=params)

        if not response_data:
            print(f"Could not fetch details for message ID {message_id}. Response was empty or API call failed.")
            return None

        # Consolidate body content
        body_content = ""
        if response_data.get('body') and response_data['body'].get('content'):
            body_content = response_data['body']['content']
        elif response_data.get('bodyPreview'):
            body_content = response_data['bodyPreview']
        
        # Determine the primary email address to reply to from the 'from' field.
        original_sender_email = None
        original_sender_name = "N/A"
        if response_data.get('from') and response_data['from'].get('emailAddress'):
            original_sender_email = response_data['from']['emailAddress'].get('address')
            original_sender_name = response_data['from']['emailAddress'].get('name', 'N/A')
        elif response_data.get('sender') and response_data['sender'].get('emailAddress'): # Fallback
            original_sender_email = response_data['sender']['emailAddress'].get('address')
            original_sender_name = response_data['sender']['emailAddress'].get('name', 'N/A')

        extracted_details = {
            "id": response_data.get("id"),
            "subject": response_data.get("subject"),
            "consolidated_body": body_content,
            "reply_to_address": original_sender_email,
            "from_name": original_sender_name,
            "from_address": original_sender_email, # Redundant but can be useful for some schemas
            "to_recipients": response_data.get("toRecipients"),
            "cc_recipients": response_data.get("ccRecipients"),
            "conversation_id": response_data.get("conversationId")
        }
        
        print(f"Successfully fetched and processed details for message ID {message_id}. Reply-to address: {original_sender_email}")
        return extracted_details

    except Exception as e:
        print(f"Error in get_email_details for message ID {message_id}: {e}")
        return None

# --- Test functions ---
def _test_get_folder_ids(folders_to_test_config):
    print("\n--- Testing Folder ID Retrieval ---")
    folder_ids = {}
    
    inbox_id = get_folder_id("Inbox") 
    if inbox_id:
        folder_ids["Inbox"] = inbox_id
    else:
        print("CRITICAL: Could not find Inbox.")

    for item in folders_to_test_config:
        folder_name = item["name"]
        is_subfolder_of_inbox = item.get("is_subfolder_of_inbox", False)
        parent_id_to_use = None

        if folder_name == "Inbox": 
            continue 

        if is_subfolder_of_inbox:
            if inbox_id:
                parent_id_to_use = inbox_id
                print(f"Attempting to find '{folder_name}' as a subfolder of Inbox...")
            else:
                print(f"Skipping search for '{folder_name}' as Inbox ID was not found.")
                continue
            
        folder_id = get_folder_id(folder_name, parent_folder_id=parent_id_to_use)
        
        if folder_id:
            folder_ids[folder_name] = folder_id
        else:
            print(f"Could not retrieve or find folder: {folder_name}")
            
    return folder_ids

def _test_get_and_move_emails(target_folder_id_map):
    print("\n--- Testing Email Retrieval, Attachments, and Move ---")
    if not target_folder_id_map.get("Needs Attention"):
        print("Cannot run email move test: 'Needs Attention' folder ID not found.")
        return

    destination_folder_for_test = target_folder_id_map["Needs Attention"]
    
    unread_emails = get_unread_emails(folder_id="inbox", top_n=1) 
    if unread_emails:
        email_to_move = unread_emails[0]
        email_id = email_to_move['id']
        print(f"Found email to test: Subject: '{email_to_move.get('subject', 'N/A')}', ID: {email_id}")

        print(f"  Testing get_email_attachments for message ID: {email_id}")
        attachments = get_email_attachments(email_id)
        if attachments:
            for att in attachments:
                print(f"    - Attachment Name: {att.get('name')}, Type: {att.get('contentType')}, Size: {att.get('size')}")
        else:
            print(f"    No non-inline attachments found for message {email_id} or an error occurred.")

        # print(f"  Attempting to move email ID {email_id} to 'Needs Attention' folder...")
        # if move_email(email_id, destination_folder_for_test):
        #     print(f"Test: Successfully initiated move for email ID {email_id} to 'Needs Attention'.")
        #     print("Please verify in Outlook.")
        # else:
        #     print(f"Test: Failed to move email ID {email_id}.")
        print("Move test part is currently commented out in the test function. Uncomment to test moving.")
    else:
        print("No unread emails in Inbox to test moving.")


import os
import base64
from pathlib import Path
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

PROJECT_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(PROJECT_ROOT / ".env")

CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REFRESH_TOKEN = os.getenv("GOOGLE_REFRESH_TOKEN")

SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.labels",
    "https://www.googleapis.com/auth/gmail.readonly"
]

def get_gmail_service():
    if not REFRESH_TOKEN:
        raise ValueError("GOOGLE_REFRESH_TOKEN is missing from .env")

    creds = Credentials(
        token=None,
        refresh_token=REFRESH_TOKEN,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        scopes=SCOPES
    )

    return build("gmail", "v1", credentials=creds)

def get_email_body(payload):
    """Recursively extracts the plain text body from the email payload."""
    # If the email is multipart, iterate through the parts
    if 'parts' in payload:
        for part in payload['parts']:
            if part['mimeType'] == 'text/plain':
                data = part['body'].get('data')
                if data:
                    return base64.urlsafe_b64decode(data).decode('utf-8')
            elif 'parts' in part:
                # Handle nested multiparts
                return get_email_body(part)
    # If the email is a single part (not multipart)
    else:
        data = payload.get('body', {}).get('data')
        if data:
            return base64.urlsafe_b64decode(data).decode('utf-8')
            
    return "No plain text body found."

def fetch_latest_emails(max_results: int = 5):
    service = get_gmail_service()
    
    results = service.users().messages().list(userId="me", maxResults=max_results).execute()
    messages = results.get("messages", [])

    if not messages:
        return []

    email_list = []
    
    for msg in messages:
        # Changed format to 'full' to get the body payload
        msg_data = service.users().messages().get(
            userId="me", id=msg["id"], format="full"
        ).execute()
        
        payload = msg_data.get("payload", {})
        headers = payload.get("headers", [])
        
        subject = next((h["value"] for h in headers if h["name"] == "Subject"), "No Subject")
        sender = next((h["value"] for h in headers if h["name"] == "From"), "Unknown")
        
        # Extract and decode the body
        body = get_email_body(payload)
        
        email_list.append({
            "id": msg["id"],
            "subject": subject,
            "from": sender,
            "body": body
        })
        
    return email_list

def fetch_unread_inbox_emails(max_results: int = 5):
    service = get_gmail_service()
    
    # The 'q' parameter filters exactly like the Gmail search bar
    search_query = "is:unread in:inbox"
    
    results = service.users().messages().list(
        userId="me", 
        maxResults=max_results, 
        q=search_query  
    ).execute()
    
    messages = results.get("messages", [])

    if not messages:
        return []

    email_list = []
    
    for msg in messages:
        msg_data = service.users().messages().get(
            userId="me", id=msg["id"], format="full"
        ).execute()
        
        payload = msg_data.get("payload", {})
        headers = payload.get("headers", [])
        
        subject = next((h["value"] for h in headers if h["name"] == "Subject"), "No Subject")
        sender = next((h["value"] for h in headers if h["name"] == "From"), "Unknown")
        
        # Extract the Cc header (defaults to an empty string if no one is CC'd)
        cc = next((h["value"] for h in headers if h["name"] == "Cc"), "")
        
        body = get_email_body(payload)
        
        email_list.append({
            "id": msg["id"],
            "subject": subject,
            "from": sender,
            "cc": cc,
            "body": body
        })
        
    # Optional: Reverse the list in Python if you want them ordered oldest-to-newest among these 5
    email_list.reverse() 
        
    return email_list

def get_all_labels():
    """Fetches all existing labels (folders and tags) from the Gmail account."""
    service = get_gmail_service()
    
    results = service.users().labels().list(userId="me").execute()
    return results.get("labels", [])


def create_label(label_path: str):
    """
    Creates a label or nested sub-label.
    Use forward slashes for nesting: e.g., 'Work/Invoices' or 'Personal/Finance/2026'.
    """
    service = get_gmail_service()
    
    # Strip leading/trailing slashes and whitespace
    clean_name = label_path.strip().strip("/")
    
    new_label = {
        "name": clean_name,
        "labelListVisibility": "labelShow",
        "messageListVisibility": "show"
    }
    
    try:
        created_label = service.users().labels().create(userId="me", body=new_label).execute()
        return created_label
    except HttpError as error:
        if error.resp.status == 409:
            raise ValueError(f"The label '{clean_name}' already exists.")
        raise ValueError(f"An error occurred while creating label: {error}")

def create_label_hierarchy(label_path: str) -> dict:
    """
    Creates nested sub-labels step-by-step so each tier expands one by one.
    Example: 'Work/Projects/ClientA' creates:
      1. 'Work'
      2. 'Work/Projects'
      3. 'Work/Projects/ClientA'
    Returns the dict of the final (deepest) created label.
    """
    service = get_gmail_service()
    
    # 1. Fetch existing labels to avoid redundant API calls
    existing_labels = service.users().labels().list(userId="me").execute().get("labels", [])
    existing_names = {label["name"].lower(): label for label in existing_labels}

    # 2. Split path segments: 'Work/Projects/ClientA' -> ['Work', 'Projects', 'ClientA']
    parts = [segment.strip() for segment in label_path.strip("/").split("/") if segment.strip()]
    if not parts:
        raise ValueError("Invalid label path provided.")

    current_path = ""
    last_label_obj = None

    for part in parts:
        current_path = f"{current_path}/{part}" if current_path else part
        lookup_key = current_path.lower()

        if lookup_key in existing_names:
            last_label_obj = existing_names[lookup_key]
            continue

        # 3. Create the missing level
        body = {
            "name": current_path,
            "labelListVisibility": "labelShow",
            "messageListVisibility": "show"
        }
        
        try:
            created = service.users().labels().create(userId="me", body=body).execute()
            existing_names[lookup_key] = created
            last_label_obj = created
        except HttpError as err:
            if err.resp.status == 409:  # Already created concurrently
                continue
            raise ValueError(f"Failed to create step '{current_path}': {err}")

    return last_label_obj


def update_email_labels(message_id: str, labels_to_add: list[str] = None, labels_to_remove: list[str] = None):
    """
    Updates the labels on a specific email. 
    Accepts label NAMES (e.g. "Work", "INBOX"). 
    Automatically creates missing labels before applying them.
    """
    service = get_gmail_service()
    
    labels_to_add = labels_to_add or []
    labels_to_remove = labels_to_remove or []
    
    # 1. Get all current labels so we can map Names to internal Google IDs
    existing_labels = get_all_labels()
    name_to_id = {label["name"].lower(): label["id"] for label in existing_labels}
    
    add_label_ids = []
    remove_label_ids = []
    
    # 2. Map 'Add' label names to IDs (and create if they don't exist)
    for name in labels_to_add:
        if not name:
            continue
        lower_name = name.lower()
        if lower_name in name_to_id:
            add_label_ids.append(name_to_id[lower_name])
        else:
            # Label doesn't exist, create it on the fly
            new_label = create_label(name)
            add_label_ids.append(new_label["id"])
            name_to_id[lower_name] = new_label["id"] # Cache it in case it's referenced again
            
    # 3. Map 'Remove' label names to IDs
    for name in labels_to_remove:
        if not name:
            continue
        lower_name = name.lower()
        if lower_name in name_to_id:
            remove_label_ids.append(name_to_id[lower_name])
            
    # 4. Apply changes to the email
    body = {
        "addLabelIds": add_label_ids,
        "removeLabelIds": remove_label_ids
    }
    
    response = service.users().messages().modify(
        userId="me", 
        id=message_id, 
        body=body
    ).execute()
    
    return {
        "id": response["id"],
        "updated_label_ids": response.get("labelIds", []),
        "status": "success"
    }

def trash_email(message_id: str):
    """
    Moves an email to the Trash. 
    Can be recovered within 30 days.
    Works with your current 'gmail.modify' scope.
    """
    service = get_gmail_service()
    
    # The API returns an updated message object on success
    response = service.users().messages().trash(userId="me", id=message_id).execute()
    
    return {
        "id": response["id"],
        "status": "moved_to_trash"
    }
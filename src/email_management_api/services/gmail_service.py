import os
import base64
from pathlib import Path
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

PROJECT_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(PROJECT_ROOT / ".env")

CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REFRESH_TOKEN = os.getenv("GOOGLE_REFRESH_TOKEN")

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

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
        q=search_query  # Applied the filter here
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
        
        body = get_email_body(payload)
        
        email_list.append({
            "id": msg["id"],
            "subject": subject,
            "from": sender,
            "body": body
        })
        
    # Optional: Reverse the list in Python if you want them ordered oldest-to-newest among these 5
    email_list.reverse() 
        
    return email_list
import os
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

    # Rebuild credentials object purely from .env variables
    creds = Credentials(
        token=None,  # Leave empty; the library will fetch a new one using the refresh token
        refresh_token=REFRESH_TOKEN,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        scopes=SCOPES
    )

    return build("gmail", "v1", credentials=creds)

def fetch_latest_emails(max_results: int = 5):
    service = get_gmail_service()
    
    results = service.users().messages().list(userId="me", maxResults=max_results).execute()
    messages = results.get("messages", [])

    if not messages:
        return []

    email_list = []
    
    for msg in messages:
        msg_data = service.users().messages().get(
            userId="me", id=msg["id"], format="metadata", metadataHeaders=["Subject", "From"]
        ).execute()
        
        headers = msg_data.get("payload", {}).get("headers", [])
        subject = next((h["value"] for h in headers if h["name"] == "Subject"), "No Subject")
        sender = next((h["value"] for h in headers if h["name"] == "From"), "Unknown")
        
        email_list.append({
            "id": msg["id"],
            "subject": subject,
            "from": sender
        })
        
    return email_list
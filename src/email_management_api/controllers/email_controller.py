from fastapi import APIRouter, HTTPException
from email_management_api.services.gmail_service import fetch_latest_emails, fetch_unread_inbox_emails

email_router = APIRouter(
    prefix="/email",
    tags=["Emails"],
)

@email_router.get("/list")
async def get_emails(limit: int = 5):
    try:
        emails = fetch_latest_emails(max_results=limit)
        return {"status": "success", "data": emails}
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to fetch emails: {str(exc)}")

@email_router.get("/unread-mails")
async def unread_emails(limit: int = 5):
    try:
        emails = fetch_unread_inbox_emails(max_results=limit)
        return {"status": "success", "data": emails}
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to fetch emails: {str(exc)}")
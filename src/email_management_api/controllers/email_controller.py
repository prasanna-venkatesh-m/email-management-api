from fastapi import APIRouter, HTTPException
from email_management_api.services.gmail_service import fetch_latest_emails, fetch_unread_inbox_emails,get_all_labels, create_label

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

@email_router.get("/get-all-labels")
async def fetch_labels(limit: int = 5):
    try:
        # Now this correctly calls your service function
        labels = get_all_labels() 
        return {"status": "success", "data": labels}
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to fetch labels: {str(exc)}")

@email_router.get("/create-labels")
async def create_labels(label: str):
    try:
        # Now this correctly calls your service function
        created_label = create_label(label_name=label) 
        return {"status": "success", "data": created_label}
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to fetch labels: {str(exc)}")
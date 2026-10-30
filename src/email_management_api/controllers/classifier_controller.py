from fastapi import FastAPI, APIRouter
from email_management_api.services.classify_service import classify_and_organize_emails

classify_router = APIRouter(
    prefix='/classify',
    tags=["Classify"]
)

@classify_router.get(path='/classify-mails')
async def classify_emails():
    return classify_and_organize_emails()
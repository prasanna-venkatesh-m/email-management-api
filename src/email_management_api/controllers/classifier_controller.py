from fastapi import FastAPI, APIRouter

classify_router = APIRouter(
    prefix='/classify',
    tags=["Classify"]
)

@classify_router.get(path='/classify-mails')
async def classify_emails():
    return True
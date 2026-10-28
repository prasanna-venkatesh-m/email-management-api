from fastapi import APIRouter

email_router = APIRouter(
    prefix="/email",
    tags=["Emails"],
)

@email_router.get(path="/")
async def get_email_token():
    return "Hello"
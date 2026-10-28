from fastapi import FastAPI
from email_management_api.controllers.email_controller import email_router

app = FastAPI()

app.include_router(email_router)
from fastapi import FastAPI
from email_management_api.controllers.email_controller import email_router
from email_management_api.controllers.classifier_controller import classify_router

app = FastAPI()

app.include_router(email_router)
app.include_router(classify_router)
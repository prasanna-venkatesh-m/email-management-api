import os
from langchain_google_genai import ChatGoogleGenerativeAI

def get_gemini_client() -> ChatGoogleGenerativeAI:
    """Initializes and returns the ChatGoogleGenerativeAI client using Google AI Studio."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY is missing from environment variables.")

    return ChatGoogleGenerativeAI(
        model="gemini-3.8-flash",  # Current primary model for tools & structured output
        temperature=0,
        api_key=api_key,
    )
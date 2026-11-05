import os
from langchain_openai import ChatOpenAI

def get_openrouter_client() -> ChatOpenAI:
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY is missing from environment variables.")
        
    return ChatOpenAI(
        temperature=0,
        # Dynamically routes to an active free model that supports your requested features (tools/json)
        model="openrouter/free",
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
        default_headers={
            "HTTP-Referer": "http://localhost:8000",
            "X-Title": "Email Management API",
        }
    )
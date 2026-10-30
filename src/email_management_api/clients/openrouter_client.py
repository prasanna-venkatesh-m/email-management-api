import os
from langchain_openai import ChatOpenAI

def get_openrouter_client() -> ChatOpenAI:
    """Initializes and returns the LangChain ChatOpenAI client configured for OpenRouter."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY is missing from environment variables.")
        
    return ChatOpenAI(
        temperature=0,
        # meta-llama/llama-3.1-70b-instruct is highly reliable for tool calling on OpenRouter
        # You can also use openai/gpt-4o-mini or anthropic/claude-3.5-sonnet
        model="meta-llama/llama-3.1-70b-instruct",
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
        default_headers={
            "HTTP-Referer": "http://localhost:8000", # Optional: Your site URL
            "X-Title": "Email Management API",       # Optional: Your app name
        }
    )
import os
from langchain_groq import ChatGroq

def get_groq_client() -> ChatGroq:
    """Initializes and returns the LangChain ChatGroq client."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY is missing from environment variables.")
        
    return ChatGroq(
        temperature=0,
        model_name="openai/gpt-oss-120b",
        api_key=api_key,
    )
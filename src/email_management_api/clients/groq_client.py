# from langchain_openai import ChatOpenAI

# def get_groq_client() -> ChatOpenAI:
#     """
#     Initializes and returns the local LM Studio LLM client.
#     """

#     return ChatOpenAI(
#         base_url="http://localhost:1235/v1",
#         api_key="lm-studio",  # LM Studio does not require a real API key
#         model="qwen3-14b",
#         temperature=0,
#         timeout=300,
#         max_retries=2,
#     )

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
from langchain_openai import ChatOpenAI

def get_groq_client() -> ChatOpenAI:
    """
    Initializes and returns the local LM Studio LLM client.
    """

    return ChatOpenAI(
        base_url="http://localhost:1235/v1",
        api_key="lm-studio",  # LM Studio does not require a real API key
        model="qwen2.5-coder-7b-instruct",
        temperature=0,
        timeout=120,
        max_retries=2,
    )

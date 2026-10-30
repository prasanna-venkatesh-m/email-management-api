from email_management_api.services.gmail_service import create_label, get_all_labels
from langchain_core.tools import tool

@tool
def check_existing_labels() -> list[str]:
    """Use this tool FIRST to fetch all existing Gmail labels/folders. Returns a list of label names."""
    labels = get_all_labels()
    return [label["name"] for label in labels]

@tool
def create_new_label(label_name: str) -> dict:
    """Use this tool to create a new Gmail label if the label you want to apply does not exist."""
    return create_label(label_name)
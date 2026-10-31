from langchain_core.tools import tool
from email_management_api.services.gmail_service import get_all_labels, create_label_hierarchy

@tool
def check_existing_labels() -> list[str]:
    """Use this tool FIRST to fetch all existing Gmail labels/folders. Returns a list of label names."""
    labels = get_all_labels()
    return [label["name"] for label in labels]

@tool
def create_new_label(name: str = None, label_path: str = None, **kwargs) -> dict:
    """
    Creates expandable nested labels step-by-step in Gmail.
    Format paths using forward slashes: 'Category/SubCategory/Topic'.
    Every level is created individually so it can be expanded tier by tier.
    Examples:
      - 'Work/Clients/Acme'
      - 'Notifications/Azure/BuildSuccess'
    """
    target = name or label_path or kwargs.get("label_name")
    if not target:
        raise ValueError("Missing label path or name argument.")
    return create_label_hierarchy(target)
from pydantic import BaseModel, Field

class EmailClassification(BaseModel):
    category: str = Field(description="The general category (e.g., Work, Finance, Spam, Personal)")
    labels_to_add: list[str] = Field(description="Exact names of labels to apply.")
    labels_to_remove: list[str] = Field(description="Exact names of labels to remove (e.g., INBOX, UNREAD).")
    is_action_required: bool = Field(description="True if the email requires a reply or action.")
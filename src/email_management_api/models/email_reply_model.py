from pydantic import BaseModel, Field
from typing import List, Optional


class EmailReply(BaseModel):
    to: List[str] = Field(
        description="Email addresses of the recipients to reply to."
    )

    cc: List[str] = Field(
        default_factory=list,
        description="CC recipients for the reply, if applicable."
    )

    subject: Optional[str] = Field(
        default=None,
        description="Reply subject. Use Re: original subject for replies. "
                    "Return None only if no subject is required."
    )

    content: str = Field(
        description="Complete email reply body, ready to be copied and sent."
    )
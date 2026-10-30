from email_management_api.services.gmail_service import (
    fetch_unread_inbox_emails,
    update_email_labels,
)
from email_management_api.services.llm_service import classify_mail


def classify_and_organize_emails(max_results: int = 5):
    unread_mails = fetch_unread_inbox_emails(max_results=max_results)
    results = []

    for mail in unread_mails:
        classification = classify_mail(
            subject=mail.get("subject", ""),
            body=mail.get("body", "")
        )

        # 1. Update mail dict with matching model attributes
        mail["category"] = classification.category
        mail["labels_to_add"] = classification.labels_to_add
        mail["labels_to_remove"] = classification.labels_to_remove
        mail["is_action_required"] = classification.is_action_required

        # 2. Apply labels in Gmail
        update_email_labels(
            message_id=mail["id"],
            labels_to_add=classification.labels_to_add,
            labels_to_remove=classification.labels_to_remove
        )

        results.append(mail)

    return results
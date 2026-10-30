from email_management_api.services.gmail_service import fetch_unread_inbox_emails, update_email_labels
from email_management_api.services.llm_service import classify_mail
import time

def classify_and_organize_emails(max_results: int = 5):
    unread_mails = fetch_unread_inbox_emails(max_results=max_results)
    results = []

    for mail in unread_mails:
        classification = classify_mail(
            subject=mail.get("subject", ""),
            body=mail.get("body", "")
        )

        print(classification)

        mail["folder"] = classification.folder
        mail["tags"] = classification.tags
        mail["isReplyable"] = classification.isReplyable

        labels_to_add = [classification.folder] + [t for t in classification.tags if t != classification.folder]
        # update_email_labels(
        #     message_id=mail["id"],
        #     labels_to_add=labels_to_add,
        #     labels_to_remove=classification.labels_to_remove
        # )

        results.append(mail)

        # PAUSE for 3 seconds before hitting the Groq API again to avoid TPM limits
        time.sleep(3) 

    return results
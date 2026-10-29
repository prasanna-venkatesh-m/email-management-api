from email_management_api.services.gmail_service import fetch_unread_inbox_emails
from email_management_api.services.llm_service import classify_mail

def classify_emails():
    unread_mails = fetch_unread_inbox_emails(max_results=5)
    result = []

    for mail in unread_mails:
        classification = classify_mail(mail)

        mail["tags"] = classification["tags"]
        mail["folder"] = classification["folder"]
        mail["isReplyable"] = classification["isReplyable"]

        result.append(mail)

    return result
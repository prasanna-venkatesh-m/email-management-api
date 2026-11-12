import logging
from email_management_api.services.gmail_service import (
    fetch_unread_inbox_emails,
    update_email_labels,
    create_draft,
    get_all_labels
)
from email_management_api.services.llm_service import (
    classify_mail,
    generate_email_reply,
)

logger = logging.getLogger(__name__)


def classify_and_organize_emails(max_results: int = 5, force_draft: bool = False):
    unread_mails = fetch_unread_inbox_emails(max_results=max_results)
    all_labels = get_all_labels()
    label_names = ", ".join(label["name"] for label in all_labels)
    print(label_names)
    results = []
    draft_mails = []

    for mail in unread_mails:
        classification = classify_mail(
            fromMailId=mail.get("from", ""),
            subject=mail.get("subject", ""),
            body=mail.get("body", ""),
            existing_labels=label_names
        )

        mail["category"] = classification.category
        mail["labels_to_add"] = classification.labels_to_add
        mail["labels_to_remove"] = classification.labels_to_remove
        mail["is_action_required"] = classification.is_action_required

        # Apply labels in Gmail
        update_email_labels(
            message_id=mail["id"],
            labels_to_add=classification.labels_to_add,
            labels_to_remove=classification.labels_to_remove,
        )

        results.append(mail)

        # Flag for drafting
        if classification.is_action_required or force_draft:
            draft_mails.append(mail)

    # Capture draft results rather than silently discarding them
    if draft_mails:
        logger.info(f"Drafting replies for {len(draft_mails)} emails...")
        draft_results = draft_emails(draft_mails)
        logger.info(f"Draft creation results: {draft_results}")
    else:
        logger.info("No emails met the 'is_action_required' condition for drafting.")

    return results


def draft_emails(mails: list[dict], user_context: str | None = None) -> list[dict]:
    created_drafts = []

    for mail in mails:
        mail_id = mail.get("id", "unknown")
        try:
            # 1. Generate LLM reply structure
            reply_obj = generate_email_reply(
                email_id=mail_id,
                from_email=mail.get("from", ""),
                cc=mail.get("cc") if isinstance(mail.get("cc"), list) else [],
                subject=mail.get("subject", ""),
                body=mail.get("body", ""),
                user_context=user_context,
            )

            # 2. Extract plain text body from the EmailReply model
            reply_body = (
                getattr(reply_obj, "content", None)
                or getattr(reply_obj, "body", None)
                or (reply_obj.get("content") or reply_obj.get("body") if isinstance(reply_obj, dict) else "")
            )

            # 3. Determine subject
            reply_subject = getattr(reply_obj, "subject", None)
            if not reply_subject:
                original_subject = mail.get("subject", "")
                reply_subject = (
                    original_subject
                    if original_subject.lower().startswith("re:")
                    else f"Re: {original_subject}"
                )

            # 4. Determine recipients
            reply_to = mail.get("from")
            reply_cc = getattr(reply_obj, "cc", None) or mail.get("cc", [])

            # 5. Create draft in Gmail
            draft = create_draft(
                thread_id=mail.get("threadId"),
                to=reply_to,
                cc=reply_cc,
                subject=reply_subject,
                body=reply_body,
            )

            draft_id = draft.get("id") if isinstance(draft, dict) else getattr(draft, "id", None)
            created_drafts.append({
                "email_id": mail_id,
                "draft_id": draft_id,
                "status": "created",
            })

        except Exception as e:
            logger.exception(f"Failed to create draft for email {mail_id}")
            created_drafts.append({
                "email_id": mail_id,
                "error": str(e),
                "status": "failed",
            })

    return created_drafts
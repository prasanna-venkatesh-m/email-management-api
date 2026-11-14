
# import json
# from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
# from email_management_api.prompts.email_classification_prompt import EMAIL_CLASSIFICATION_PROMPT
# from email_management_api.clients.openrouter_client import get_openrouter_client
# from email_management_api.clients.gemini_client import get_gemini_client
# from email_management_api.tools.gmail_tools import create_new_label, check_existing_labels
# from email_management_api.models.email_classification_model import EmailClassification


# def classify_mail(subject: str, body: str, max_iterations: int = 6) -> EmailClassification:
#     # llm = get_openrouter_client()
#     llm = get_gemini_client()
#     tools = [check_existing_labels, create_new_label]
#     tool_map = {tool.name: tool for tool in tools}

#     safe_body = body[:3000] + ("..." if len(body) > 3000 else "")

#     llm_with_tools = llm.bind_tools(tools)

#     messages = [
#         SystemMessage(content=EMAIL_CLASSIFICATION_PROMPT),
#         HumanMessage(content=f"Subject: {subject}\n\nBody: {safe_body}"),
#     ]

#     labels_checked = False

#     for _ in range(max_iterations):
#         response = llm_with_tools.invoke(messages)
#         messages.append(response)

#         if not response.tool_calls:
#             break

#         for tool_call in response.tool_calls:
#             tool_name = tool_call["name"]

#             if tool_name == "create_new_label" and not labels_checked:
#                 raise RuntimeError("Check existing labels first.")

#             result = tool_map[tool_name].invoke(tool_call["args"])

#             if tool_name == "check_existing_labels":
#                 labels_checked = True

#             messages.append(
#                 ToolMessage(
#                     content=json.dumps(result, default=str),
#                     tool_call_id=tool_call["id"],
#                 )
#             )

#     if not labels_checked:
#         result = check_existing_labels.invoke({})
#         messages.append(
#             ToolMessage(
#                 content=json.dumps(result, default=str),
#                 tool_call_id="label_check",
#             )
#         )

#     structured_llm = llm.with_structured_output(EmailClassification)

#     return structured_llm.invoke([
#         SystemMessage(content="Return the final email classification using the EmailClassification schema. Use only verified existing or successfully created labels."),
#         *messages[1:],
#     ])


import json

from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage

from email_management_api.prompts.email_classification_prompt import (
    EMAIL_CLASSIFICATION_PROMPT,
)
from email_management_api.prompts.email_reply_prompt import (
    EMAIL_REPLY_PROMPT,
)

from email_management_api.clients.groq_client import get_groq_client

from email_management_api.tools.gmail_tools import (
    create_new_label,
    check_existing_labels,
)

from email_management_api.models.email_classification_model import EmailClassification
from email_management_api.models.email_reply_model import EmailReply


def classify_mail(
    fromMailId: str,
    subject: str,
    body: str,
    existing_labels : str,
    sender_type: str,
    max_iterations: int = 6
) -> EmailClassification:

    llm = get_groq_client()

    tools = [create_new_label]
    tool_map = {tool.name: tool for tool in tools}

    safe_body = body[:3000] + ("..." if len(body) > 3000 else "")

    llm_with_tools = llm.bind_tools(tools)

    messages = [
        SystemMessage(content=EMAIL_CLASSIFICATION_PROMPT),
        HumanMessage(content=f"Existing Labels: {existing_labels}\n\n From: {fromMailId}\n\n  SENDER_TYPE: {sender_type}\n\n Subject: {subject}\n\nBody: {safe_body}"),
    ]

    labels_checked = False

    # PHASE 1: Tool execution loop
    for _ in range(max_iterations):

        response = llm_with_tools.invoke(messages)
        messages.append(response)

        tool_calls = getattr(response, "tool_calls", None) or []

        if not tool_calls:
            break

        for tool_call in tool_calls:

            if isinstance(tool_call, dict):

                tool_name = (
                    tool_call.get("name")
                    or tool_call.get("function", {}).get("name")
                )

                raw_args = tool_call.get("args")

                if raw_args is None and "function" in tool_call:
                    arg_str = tool_call["function"].get("arguments", "{}")
                    tool_args = (
                        json.loads(arg_str)
                        if isinstance(arg_str, str)
                        else arg_str
                    )
                else:
                    tool_args = raw_args or {}

                call_id = tool_call.get("id", "call_default")

            else:
                tool_name = getattr(tool_call, "name", None)
                tool_args = getattr(tool_call, "args", {})
                call_id = getattr(tool_call, "id", "call_default")

            if not tool_name or tool_name not in tool_map:
                continue

            if tool_name == "create_new_label" and not labels_checked:

                messages.append(
                    ToolMessage(
                        content="Error: Execute check_existing_labels first.",
                        tool_call_id=call_id,
                    )
                )
                continue

            try:

                result = tool_map[tool_name].invoke(tool_args)

                if tool_name == "check_existing_labels":
                    labels_checked = True

                messages.append(
                    ToolMessage(
                        content=json.dumps(result, default=str),
                        tool_call_id=call_id,
                    )
                )

            except Exception as err:

                messages.append(
                    ToolMessage(
                        content=f"Tool execution failed: {str(err)}",
                        tool_call_id=call_id,
                    )
                )

    # PHASE 2: Verify labels
    verified_labels = []

    if not labels_checked:
        try:
            verified_labels = check_existing_labels.invoke({})
        except Exception:
            verified_labels = []

    # PHASE 3: Structured classification
    structured_llm = llm.with_structured_output(EmailClassification)

    final_user_content = (
        f"Subject: {subject}\n\n"
        f"Body: {safe_body}\n\n"
        f"Verified existing labels: {json.dumps(verified_labels)}\n\n"
        "Return the final structured classification "
        "using the EmailClassification schema."
    )

    final_payload = [
        SystemMessage(
            content=(
                "You are an email classification assistant. "
                "Return the final email classification using "
                "the EmailClassification schema. "
                "Use only verified existing or successfully created labels."
            )
        ),
        HumanMessage(content=final_user_content),
    ]

    return structured_llm.invoke(final_payload)


def generate_email_reply(
    email_id: str,
    from_email: str,
    cc: list[str],
    subject: str,
    body: str,
    user_context: str | None = None
) -> EmailReply:

    llm = get_groq_client()

    structured_llm = llm.with_structured_output(EmailReply)

    safe_body = body[:5000] + ("..." if len(body) > 5000 else "")

    messages = [
        SystemMessage(content=EMAIL_REPLY_PROMPT),

        HumanMessage(
            content=f"""
Email ID: {email_id}

From: {from_email}

CC: {json.dumps(cc)}

Subject: {subject}

Body:
{safe_body}

Additional instructions from the user:
{
    user_context
    if user_context
    else "No additional instructions. Generate a suitable reply based on the email context."
}

Generate an appropriate reply draft following the user's additional instructions.
"""
        ),
    ]

    return structured_llm.invoke(messages)

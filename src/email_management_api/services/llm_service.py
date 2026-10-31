
import json
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from email_management_api.prompts.email_classification_prompt import EMAIL_CLASSIFICATION_PROMPT
from email_management_api.clients.openrouter_client import get_openrouter_client
from email_management_api.tools.gmail_tools import create_new_label, check_existing_labels
from email_management_api.models.email_classification_model import EmailClassification


def classify_mail(subject: str, body: str, max_iterations: int = 6) -> EmailClassification:
    llm = get_openrouter_client()
    tools = [check_existing_labels, create_new_label]
    tool_map = {tool.name: tool for tool in tools}

    safe_body = body[:3000] + ("..." if len(body) > 3000 else "")

    llm_with_tools = llm.bind_tools(tools)

    messages = [
        SystemMessage(content=EMAIL_CLASSIFICATION_PROMPT),
        HumanMessage(content=f"Subject: {subject}\n\nBody: {safe_body}"),
    ]

    labels_checked = False

    for _ in range(max_iterations):
        response = llm_with_tools.invoke(messages)
        messages.append(response)

        if not response.tool_calls:
            break

        for tool_call in response.tool_calls:
            tool_name = tool_call["name"]

            if tool_name == "create_new_label" and not labels_checked:
                raise RuntimeError("Check existing labels first.")

            result = tool_map[tool_name].invoke(tool_call["args"])

            if tool_name == "check_existing_labels":
                labels_checked = True

            messages.append(
                ToolMessage(
                    content=json.dumps(result, default=str),
                    tool_call_id=tool_call["id"],
                )
            )

    if not labels_checked:
        result = check_existing_labels.invoke({})
        messages.append(
            ToolMessage(
                content=json.dumps(result, default=str),
                tool_call_id="label_check",
            )
        )

    structured_llm = llm.with_structured_output(EmailClassification)

    return structured_llm.invoke([
        SystemMessage(content="Return the final email classification using the EmailClassification schema. Use only verified existing or successfully created labels."),
        *messages[1:],
    ])

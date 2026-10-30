import json
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from email_management_api.clients.openrouter_client import get_openrouter_client
from email_management_api.tools.gmail_tools import create_new_label, check_existing_labels
from email_management_api.models.email_classification_model import EmailClassification

def classify_mail(subject: str, body: str, max_iterations: int = 6) -> EmailClassification:
    llm = get_openrouter_client()
    tools = [create_new_label, check_existing_labels]
    tool_map = {tool.name: tool for tool in tools}

    # Truncate body to ensure context limits aren't exceeded
    max_chars = 3000
    safe_body = body[:max_chars] + ("..." if len(body) > max_chars else "")

    llm_with_tools = llm.bind_tools(tools)

    messages = [
        SystemMessage(content=(
            "You are an autonomous email classification assistant.\n"
            "1. First, call `check_existing_labels` to see what Gmail labels exist.\n"
            "2. If an appropriate folder or tag does not exist for this email, call `create_new_label` to make it.\n"
            "3. If all needed labels exist, or after you have created them, conclude your action."
        )),
        HumanMessage(content=f"Subject: {subject}\n\nBody: {safe_body}")
    ]

    # Phase 1: Tool loop (inspect / create labels)
    for _ in range(max_iterations):
        response = llm_with_tools.invoke(messages)
        messages.append(response)

        if not response.tool_calls:
            # Model decided no more tools need to be called
            break

        for tool_call in response.tool_calls:
            selected_tool = tool_map[tool_call["name"]]
            tool_result = selected_tool.invoke(tool_call["args"])

            messages.append(ToolMessage(
                content=json.dumps(tool_result),
                tool_call_id=tool_call["id"]
            ))

    # Phase 2: Guaranteed Structured Classification
    # with_structured_output forces OpenRouter/OpenAI to output the exact Pydantic schema
    structured_llm = llm.with_structured_output(EmailClassification)
    
    classification_prompt = [
        SystemMessage(content=(
            "Based on the email and the labels verified/created in this conversation, "
            "provide the final classification."
        )),
        *messages[1:] # Pass the email content and the tool results
    ]

    result: EmailClassification = structured_llm.invoke(classification_prompt)
    return result
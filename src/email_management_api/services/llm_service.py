
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
from email_management_api.prompts.email_classification_prompt import EMAIL_CLASSIFICATION_PROMPT
from email_management_api.clients.openrouter_client import get_openrouter_client
from email_management_api.clients.gemini_client import get_gemini_client
from email_management_api.tools.gmail_tools import create_new_label, check_existing_labels
from email_management_api.models.email_classification_model import EmailClassification


def classify_mail(subject: str, body: str, max_iterations: int = 6) -> EmailClassification:
    # Works interchangeably with get_gemini_client(), get_openrouter_client(), or get_groq_client()
    llm = get_gemini_client()
    
    tools = [check_existing_labels, create_new_label]
    tool_map = {tool.name: tool for tool in tools}

    safe_body = body[:3000] + ("..." if len(body) > 3000 else "")
    llm_with_tools = llm.bind_tools(tools)

    messages = [
        SystemMessage(content=EMAIL_CLASSIFICATION_PROMPT),
        HumanMessage(content=f"Subject: {subject}\n\nBody: {safe_body}"),
    ]

    labels_checked = False

    # --- PHASE 1: Agentic Tool-Execution Loop ---
    for _ in range(max_iterations):
        response = llm_with_tools.invoke(messages)
        messages.append(response)

        tool_calls = getattr(response, "tool_calls", None) or []
        if not tool_calls:
            # Model has gathered all information or made all necessary labels
            break

        for tool_call in tool_calls:
            # Defensive extraction compatible with Gemini, Groq, and OpenRouter formats
            if isinstance(tool_call, dict):
                tool_name = tool_call.get("name") or tool_call.get("function", {}).get("name")
                raw_args = tool_call.get("args")
                if raw_args is None and "function" in tool_call:
                    arg_str = tool_call["function"].get("arguments", "{}")
                    tool_args = json.loads(arg_str) if isinstance(arg_str, str) else arg_str
                else:
                    tool_args = raw_args or {}
                call_id = tool_call.get("id", "call_default")
            else:
                tool_name = getattr(tool_call, "name", None)
                tool_args = getattr(tool_call, "args", {})
                call_id = getattr(tool_call, "id", "call_default")

            if not tool_name or tool_name not in tool_map:
                continue

            # Soft guardrail: inform the LLM to inspect labels first without killing the server
            if tool_name == "create_new_label" and not labels_checked:
                messages.append(
                    ToolMessage(
                        content="Error: You must execute `check_existing_labels` first before creating new labels.",
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

    # --- PHASE 2: Final Classification Turn ---
    # Ensure available labels are known even if the model bypassed checking them
    verified_labels = []
    if not labels_checked:
        try:
            verified_labels = check_existing_labels.invoke({})
        except Exception:
            verified_labels = []

    structured_llm = llm.with_structured_output(EmailClassification)

    # Universal turn sequence:
    # 1. SystemMessage defines schema guidelines.
    # 2. HumanMessage is the final turn (satisfies Gemini's non-prefilling rule
    #    and avoids mismatched tool_call_id errors on Groq/OpenRouter).
    final_user_content = (
        f"Subject: {subject}\n\n"
        f"Body: {safe_body}\n\n"
        f"{('Verified existing labels: ' + json.dumps(verified_labels)) if verified_labels else ''}\n\n"
        "Return the final structured classification using the EmailClassification schema."
    )

    final_payload = [
        SystemMessage(
            content="You are an email classification assistant. Return the final email classification using the EmailClassification schema. Use only verified existing or successfully created labels."
        ),
        HumanMessage(content=final_user_content)
    ]

    return structured_llm.invoke(final_payload)
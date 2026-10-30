import json
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from email_management_api.clients.groq_client import get_groq_client
from email_management_api.clients.openrouter_client import get_openrouter_client
from email_management_api.tools.gmail_tools import create_new_label, check_existing_labels
from email_management_api.models.email_classification_model import EmailClassification

def classify_mail(subject: str, body: str, max_iterations: int = 5):
    llm = get_openrouter_client()
    tools = [create_new_label, check_existing_labels]
    
    # 1. Bind tools directly to the model
    llm_with_tools = llm.bind_tools(tools)
    
    # 2. Map tool names to actual functions for execution
    tool_map = {tool.name: tool for tool in tools}

    schema_string = json.dumps(EmailClassification.model_json_schema())

    messages = [
        SystemMessage(content=f"""
        You are an intelligent email routing assistant. Your job is to classify incoming emails and organize them using Gmail labels.
        ... (rest of your prompt) ...
        {schema_string}
        """),
        # Use safe_body here instead of the raw body
        HumanMessage(content=f"Subject: {subject}\n\nBody: {body}") 
    ]

    # --- THE AGENT LOOP ---
    for _ in range(max_iterations):
        # Let the model think and decide what to do
        response = llm_with_tools.invoke(messages)
        messages.append(response)

        # Check if the model decided to call a tool
        if response.tool_calls:
            for tool_call in response.tool_calls:
                # Execute the specific tool requested
                selected_tool = tool_map[tool_call["name"]]
                tool_result = selected_tool.invoke(tool_call["args"])
                
                # Append the result of the tool back into the conversation history
                messages.append(ToolMessage(
                    content=json.dumps(tool_result),
                    tool_call_id=tool_call["id"]
                ))
            # The loop continues, sending the tool results back to the LLM
            
        else:
            # If no tools were called, the model is done and provided the final answer
            clean_output = response.content.strip()
            
            # Clean up markdown code blocks if the model hallucinates them
            if clean_output.startswith("```json"):
                clean_output = clean_output.removeprefix("```json").removesuffix("```").strip()
            elif clean_output.startswith("```"):
                clean_output = clean_output.removeprefix("```").removesuffix("```").strip()

            return EmailClassification(**json.loads(clean_output))

    raise RuntimeError(f"Agent failed to classify within {max_iterations} iterations.")
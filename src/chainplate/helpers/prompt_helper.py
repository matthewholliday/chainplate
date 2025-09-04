from ..services.cli_animation_service import run_with_spinner
from ..services.external.prompt_completion_services.openai_llm_provider import OpenAIPromptService

CLIENT_NAME = "openai" # TODO: make configurable
OPENAI_MODEL = "gpt-5-mini" # TODO: make configurable

def ask_llm(prompt: str):
    if(CLIENT_NAME == "openai"):
        response_text = OpenAIPromptService.get_completion(chat_history=[
            {"role": "user", "content": prompt}
        ])
    return response_text

def ask_with_context(prompt: str, context: str, chat_history: list) -> str:
    if context:
        prompt = f"{context}\n\n{prompt}"

    if(CLIENT_NAME == "openai"):
        #append the latest user message to the chat history
        messages = chat_history + [{"role": "user", "content": prompt}]
        response_text = OpenAIPromptService().get_completion(chat_history=messages)

    return response_text

def ask_with_context_and_spinner(prompt: str, context: str, chat_history: list) -> str:
    return run_with_spinner(
        ask_with_context,
        prompt,
        context,
        chat_history,
        message=""
    )

def create_message(role: str, content: str) -> dict:
    return {"role": role, "content": content}

def create_user_message(content: str) -> dict:
    return create_message("user", content)

def create_assistant_message(content: str) -> dict:
    return create_message("assistant", content)

# TODO: implement system message


    



# Try to import OpenAI client in a way compatible with both v1 and v0 APIs
try:
    from openai import OpenAI
    client = OpenAI()  # v1 API
    def ask_openai(prompt: str) -> str:
        resp = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}]
        )
        return resp.choices[0].message.content
except ImportError:
    import openai
    client = openai
    def ask_openai(prompt: str) -> str:
        resp = client.ChatCompletion.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}]
        )
        return resp.choices[0].message["content"]

CLIENT_NAME = "openai" # TODO: make configurable
OPENAI_MODEL = "gpt-5-mini" # TODO: make configurable

def ask(prompt: str) -> str:
    if(CLIENT_NAME == "openai"):
        return ask_openai(prompt)
    else:
        raise ValueError(f"Unsupported client: {CLIENT_NAME}")
    
def ask_with_context(prompt: str, context: str, chat_history: list) -> str:
    if context:
        prompt = f"{context}\n\n{prompt}"
    if(CLIENT_NAME == "openai"):

        #append the latest user message to the chat history
        messages = chat_history + [{"role": "user", "content": prompt}]
        
        resp = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages
        )
    return resp.choices[0].message.content

def chat(conversation_history: list) -> list:
    if(CLIENT_NAME == "openai"):
        if isinstance(conversation_history, list):
            resp = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=conversation_history
            )
            conversation_history.append({
                "role": "assistant",
                "content": resp.choices[0].message.content
            })
            return conversation_history
        else:
            raise ValueError("conversation_history must be a list of messages")
    else:
        raise ValueError(f"Unsupported client: {CLIENT_NAME}")

def create_message(role: str, content: str) -> dict:
    return {"role": role, "content": content}

def create_user_message(content: str) -> dict:
    return create_message("user", content)

def create_assistant_message(content: str) -> dict:
    return create_message("assistant", content)

# TODO: implement system message


    


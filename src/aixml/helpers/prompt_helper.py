
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
OPENAI_MODEL = "gpt-3.5-turbo" # TODO: make configurable

def ask(prompt: str) -> str:
    if(CLIENT_NAME == "openai"):
        return ask_openai(prompt)
    else:
        raise ValueError(f"Unsupported client: {CLIENT_NAME}")

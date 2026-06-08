import json
import os
import requests
from dotenv import load_dotenv, dotenv_values

load_dotenv(override=True)
env_values = dotenv_values(".env")

OPENROUTER_API_KEY = env_values.get("OPENROUTER_API_KEY") or os.getenv("OPENROUTER_API_KEY")
OPENROUTER_ENDPOINT = (
    env_values.get("OPENROUTER_ENDPOINT")
    or os.getenv("OPENROUTER_ENDPOINT")
    or "https://openrouter.ai/api/v1/chat/completions"
)
OPENROUTER_MODEL = (
    env_values.get("OPENROUTER_MODEL")
    or os.getenv("OPENROUTER_MODEL")
    or "gpt-4o-mini"
)

if not OPENROUTER_API_KEY:
    raise RuntimeError("OPENROUTER_API_KEY not set in environment")


def build_prompt(question: str, schema_context: str) -> list:
    system_msg = "You are a MySQL expert."
    user_msg = (
        "Database Schema:\n"
        f"{schema_context}\n\n"
        "User Question:\n"
        f"{question}\n\n"
        "Rules:\n\n"
        "* Generate only SQL.\n"
        "* Use MySQL syntax.\n"
        "* Do not explain.\n"
        "* Do not use markdown.\n"
        "* Return exactly one SQL statement."
    )

    return [
        {"role": "system", "content": system_msg},
        {"role": "user", "content": user_msg},
    ]


def call_llm(messages: list, model: str = OPENROUTER_MODEL) -> str:
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.0,
        "max_tokens": 512,
    }

    response = requests.post(OPENROUTER_ENDPOINT, headers=headers, json=payload, timeout=30)
    response.raise_for_status()
    data = response.json()

    if "choices" in data and len(data["choices"]) > 0:
        content = data["choices"][0].get("message", {}).get("content")
        if content:
            return content.strip()

    if "output" in data:
        if isinstance(data["output"], list) and len(data["output"]) > 0:
            return data["output"][0].get("content", "").strip()
        if isinstance(data["output"], str):
            return data["output"].strip()

    raise RuntimeError("Unexpected response shape from LLM: " + json.dumps(data))


def generate_sql(question: str, chunks: list[dict]) -> str:
    schema_context = "\n\n".join(chunk["text"] for chunk in chunks)
    messages = build_prompt(question, schema_context)
    return call_llm(messages)

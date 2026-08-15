"""Groq — OpenAI-compatible. Quirk: usage arrives under `x_groq`, handled in
the shared transport."""

from . import openai_chat


def call(prompt, system_prompt, params):
    return openai_chat.send(params["base_url"].rstrip("/") + "/chat/completions",
                            prompt, system_prompt, params)

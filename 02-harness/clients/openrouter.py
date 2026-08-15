"""OpenRouter — OpenAI-compatible. Quirk: attribution headers, which OpenRouter
uses for free-tier ranking; omitting them is permitted but discouraged."""

from . import openai_chat

HEADERS = {
    "HTTP-Referer": "https://github.com/brajk/zero-budget-model-advisor",
    "X-Title": "Zero-Budget Model Advisor",
}


def call(prompt, system_prompt, params):
    return openai_chat.send(params["base_url"].rstrip("/") + "/chat/completions",
                            prompt, system_prompt, params, extra_headers=HEADERS)

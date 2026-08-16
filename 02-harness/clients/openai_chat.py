"""Shared transport for OpenAI-compatible /chat/completions providers.

Three of the five providers speak this wire format, which is the third
occurrence and therefore the point at which CLAUDE.md rule 2 permits the
abstraction. It is not a base class: the thin clients call `send()` with their
own endpoint, auth and quirks, and this module knows nothing about which
provider it is serving.

This module is purely a wire format. The retry policy lives in base.py,
shared with the Gemini client, which does not speak this format.
"""

import json
import os
import socket
import time
import urllib.error
import urllib.request

from . import base


def send(url, prompt, system_prompt, params, extra_headers=None):
    api_key = os.environ.get(params["api_key_env"], "")
    messages = []
    # An empty system message is not the same as no system message: some
    # providers apply a different prompt template. Omitted unless it has
    # content, so conditions stay identical across models (Decision B4).
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    body = {
        "model": params["model"],
        "messages": messages,
        "temperature": params["temperature"],
        "max_tokens": params["max_tokens"],
        "stream": True,
        "stream_options": {"include_usage": True},
    }
    headers = {"Content-Type": "application/json",
               "Authorization": "Bearer " + api_key,
               "User-Agent": base.USER_AGENT}
    headers.update(extra_headers or {})

    queue_wait_ms = base.pace(params["min_interval_s"])
    rate_limit_attempts = 0
    server_error_retries = 0
    retry_count = 0

    while True:
        started = time.monotonic()
        try:
            return _read_stream(url, body, headers, params, started,
                                queue_wait_ms, retry_count)
        except urllib.error.HTTPError as error:
            error_raw = error.read().decode(errors="replace")
            if error.code == 429 or "quota" in error_raw.lower():
                if rate_limit_attempts < len(base.BACKOFF_S):
                    # Backoff is harness-side waiting, so it belongs in
                    # queue_wait_ms, never folded into latency_ms — a limited
                    # model and a slow model are different findings (§2).
                    queue_wait_ms += base.sleep(base.retry_after(error, rate_limit_attempts))
                    rate_limit_attempts += 1
                    retry_count += 1
                    continue
                return base.failure(error_raw, error.code, base.RATE_LIMIT,
                                started, queue_wait_ms, retry_count)
            if 500 <= error.code < 600 and server_error_retries < base.MAX_5XX_RETRIES:
                server_error_retries += 1
                retry_count += 1
                continue
            return base.failure(error_raw, error.code, base.API_ERROR,
                            started, queue_wait_ms, retry_count)
        except socket.timeout:
            # A timeout is a result, not an accident. Never retried.
            return base.failure("timeout after %ss" % params["timeout_s"], 0,
                            base.TIMEOUT, started, queue_wait_ms, retry_count)
        except urllib.error.URLError as error:
            return base.failure(str(error.reason), 0, base.API_ERROR,
                            started, queue_wait_ms, retry_count)


def _read_stream(url, body, headers, params, started, queue_wait_ms, retry_count):
    request = urllib.request.Request(url, data=json.dumps(body).encode(), headers=headers)
    chunks = []
    first_token_ms = 0
    finish_reason = ""
    usage = {}
    model_version = ""

    with urllib.request.urlopen(request, timeout=params["timeout_s"]) as response:
        http_status = response.status
        for line in response:
            line = line.decode(errors="replace").strip()
            if not line.startswith("data:"):
                continue
            payload = line[len("data:"):].strip()
            if payload == "[DONE]":
                break
            event = json.loads(payload)
            model_version = event.get("model", model_version)
            # Groq nests usage under x_groq; everyone else puts it top level.
            usage = event.get("usage") or event.get("x_groq", {}).get("usage") or usage
            for choice in event.get("choices", []):
                piece = choice.get("delta", {}).get("content") or ""
                if piece and not chunks:
                    first_token_ms = int((time.monotonic() - started) * 1000)
                if piece:
                    chunks.append(piece)
                finish_reason = choice.get("finish_reason") or finish_reason

    latency_ms = int((time.monotonic() - started) * 1000)
    text = "".join(chunks)

    tokens_in = (usage or {}).get("prompt_tokens", 0)
    tokens_out = (usage or {}).get("completion_tokens", 0)
    tokens_estimated = not usage
    if tokens_estimated:
        # Spec §2: a missing token count must be estimated and flagged, never
        # left at zero — cost projection and breakeven depend on it.
        # Floored at 1: a request that was sent had input, so tokens_in: 0
        # would be factually false in the raw record.
        tokens_in = max(1, sum(len(m["content"]) for m in body["messages"]) // 4)
        tokens_out = max(1, len(text) // 4)

    failure_code = ""
    if not text.strip():
        failure_code = base.EMPTY
    elif finish_reason == "length":
        failure_code = base.TRUNCATION

    return base.CallResult(
        response_text=text,
        finish_reason=finish_reason,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        tokens_estimated=tokens_estimated,
        http_status=http_status,
        model_version=model_version,
        latency_ms=latency_ms,
        time_to_first_token_ms=first_token_ms,
        queue_wait_ms=queue_wait_ms,
        status="failure" if failure_code else "success",
        failure_code=failure_code,
        error_raw="",
        retry_count=retry_count,
    )

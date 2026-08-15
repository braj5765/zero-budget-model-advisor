"""Gemini — its own wire format: key in the query string, `systemInstruction`
separate from contents, `usageMetadata` on the final SSE event."""

import json
import os
import socket
import time
import urllib.error
import urllib.request

from . import base


def call(prompt, system_prompt, params):
    api_key = os.environ.get(params["api_key_env"], "")
    url = "%s/models/%s:streamGenerateContent?alt=sse&key=%s" % (
        params["base_url"].rstrip("/"), params["model"], api_key)

    body = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": params["temperature"],
            "maxOutputTokens": params["max_tokens"],
        },
    }
    # Omitted unless it has content — same rule as the OpenAI-compatible
    # transport, for the same reason (Decision B4).
    if system_prompt:
        body["systemInstruction"] = {"parts": [{"text": system_prompt}]}

    headers = {"Content-Type": "application/json", "User-Agent": base.USER_AGENT}
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
            # Gemini signals free-tier exhaustion as RESOURCE_EXHAUSTED, which
            # arrives as 429 but is worth matching on the body too.
            if error.code == 429 or "RESOURCE_EXHAUSTED" in error_raw:
                if rate_limit_attempts < len(base.BACKOFF_S):
                    queue_wait_ms += base.sleep(
                        base.retry_after(error, rate_limit_attempts))
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
            event = json.loads(line[len("data:"):].strip())
            usage = event.get("usageMetadata", usage)
            model_version = event.get("modelVersion", model_version)
            for candidate in event.get("candidates", []):
                for part in candidate.get("content", {}).get("parts", []):
                    piece = part.get("text", "")
                    if piece and not chunks:
                        first_token_ms = int((time.monotonic() - started) * 1000)
                    if piece:
                        chunks.append(piece)
                finish_reason = candidate.get("finishReason") or finish_reason

    latency_ms = int((time.monotonic() - started) * 1000)
    text = "".join(chunks)

    tokens_in = usage.get("promptTokenCount", 0)
    tokens_out = usage.get("candidatesTokenCount", 0)
    tokens_estimated = not usage
    if tokens_estimated:
        tokens_in = max(1, len(_prompt_of(body)) // 4)
        tokens_out = max(1, len(text) // 4)

    failure_code = ""
    if not text.strip():
        failure_code = base.EMPTY
    elif finish_reason == "MAX_TOKENS":
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


def _prompt_of(body):
    return body["contents"][0]["parts"][0]["text"]

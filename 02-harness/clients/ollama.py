"""Ollama client — local, no key, no quota. Streams so TTFT is measured, not null."""

import json
import socket
import time
import urllib.error
import urllib.request

from . import base


def call(prompt, system_prompt, params):
    queue_wait_ms = base.pace(params["min_interval_s"])
    retry_count = 0

    while True:
        result = _attempt(prompt, system_prompt, params, queue_wait_ms, retry_count)
        # 5xx only: up to 3 retries, then API_ERROR (Harness-Spec §3). A timeout
        # is a result, not an accident, and an empty response is a finding —
        # neither is retried.
        #
        # No 429/exponential backoff here, deliberately: Ollama is local and has
        # no quota, so RATE_LIMIT is unreachable on this transport. §3 assigns
        # the backoff policy to clients that need it, not to every client. Do
        # not "fix" this by adding backoff that can never execute.
        if result.failure_code == base.API_ERROR and retry_count < params["max_retries"]:
            retry_count += 1
            continue
        return result


def _attempt(prompt, system_prompt, params, queue_wait_ms, retry_count):
    body = {
        "model": params["model"],
        "prompt": prompt,
        "stream": True,
        "options": {
            "temperature": params["temperature"],
            "num_predict": params["max_tokens"],
        },
    }
    if system_prompt:
        body["system"] = system_prompt

    request = urllib.request.Request(
        params["base_url"].rstrip("/") + "/api/generate",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
    )

    chunks = []
    first_token_ms = 0
    final = {}
    started = time.monotonic()
    try:
        with urllib.request.urlopen(request, timeout=params["timeout_s"]) as response:
            http_status = response.status
            for line in response:
                if not line.strip():
                    continue
                event = json.loads(line)
                piece = event.get("response", "")
                if piece and not chunks:
                    first_token_ms = int((time.monotonic() - started) * 1000)
                chunks.append(piece)
                if event.get("done"):
                    final = event
    except urllib.error.HTTPError as error:
        return base.failure(error.read().decode(errors="replace"), error.code,
                            base.API_ERROR, started, queue_wait_ms, retry_count)
    except socket.timeout:
        return base.failure("timeout after %ss" % params["timeout_s"], 0,
                        base.TIMEOUT, started, queue_wait_ms, retry_count)
    except urllib.error.URLError as error:
        return base.failure(str(error.reason), 0, base.API_ERROR,
                        started, queue_wait_ms, retry_count)

    latency_ms = int((time.monotonic() - started) * 1000)
    text = "".join(chunks)
    done_reason = final.get("done_reason", "")

    failure_code = ""
    if not text.strip():
        failure_code = base.EMPTY
    elif done_reason == "length":
        failure_code = base.TRUNCATION

    return base.CallResult(
        response_text=text,
        finish_reason=done_reason,
        tokens_in=final.get("prompt_eval_count", 0),
        tokens_out=final.get("eval_count", 0),
        tokens_estimated=False,          # Ollama reports both natively
        http_status=http_status,
        model_version=final.get("model", ""),
        latency_ms=latency_ms,
        time_to_first_token_ms=first_token_ms,
        queue_wait_ms=queue_wait_ms,
        status="failure" if failure_code else "success",
        failure_code=failure_code,
        error_raw="",
        retry_count=retry_count,
    )

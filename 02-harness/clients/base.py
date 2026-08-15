"""Shared client contract: call(prompt, system_prompt, params) -> CallResult,
plus the one retry policy (Harness-Spec §3) that all clients share.

The contract is the abstraction justified up front (§6), because there are five
implementations on day one. The retry policy joined it once four clients needed
it — §3 says one policy, and one policy lives in one place rather than being
reached for across a private boundary in whichever module happened to define it.
"""

import time
from dataclasses import dataclass

# The transport half of the failure taxonomy. Scoring-Rubric.md §6 is the
# canonical list of all eight codes; the other three — REFUSAL, MALFORMED,
# HALLUCINATION — require reading the content, so they live in
# 04-analysis/scoring/failure_codes.py and must never be set here. A client
# that set them would be scoring inside the transport layer.
RATE_LIMIT = "RATE_LIMIT"
TIMEOUT = "TIMEOUT"
TRUNCATION = "TRUNCATION"
EMPTY = "EMPTY"
API_ERROR = "API_ERROR"


@dataclass
class CallResult:
    """One provider call's response, timing and outcome (Harness-Spec §2).

    Identity, request and run-context fields are the runner's to attach; a
    client knows nothing about case_id or run_id.
    """

    # Response
    response_text: str          # raw and unmodified — fences and preambles survive
    finish_reason: str
    tokens_in: int
    tokens_out: int
    tokens_estimated: bool
    http_status: int
    model_version: str          # free tiers swap versions silently

    # Timing
    latency_ms: int             # request sent -> response complete
    time_to_first_token_ms: int
    queue_wait_ms: int          # harness-side backoff, deliberately not in latency_ms

    # Outcome
    status: str                 # "success" | "failure"
    failure_code: str
    error_raw: str              # the provider's own message, verbatim
    retry_count: int


# --- Retry policy (Harness-Spec §3), shared by every client ---
#
# 429/quota -> exponential backoff honouring Retry-After, max 5 attempts, then
# RATE_LIMIT. 5xx -> up to 3 retries, then API_ERROR. Timeout -> never retried.
# Refusal, empty and malformed -> never retried; those are the findings.
BACKOFF_S = [2, 4, 8, 16, 32]
MAX_5XX_RETRIES = 3

# Groq sits behind Cloudflare, which rejects urllib's default User-Agent with
# HTTP 403 error 1010 before the request ever reaches the API. Sent by every
# client so the harness identifies itself honestly rather than by omission.
USER_AGENT = "zero-budget-model-advisor/1.0 (benchmark harness)"


def pace(min_interval_s):
    """Unconditional inter-request delay from config. Returns queue_wait_ms."""
    if min_interval_s <= 0:
        return 0
    time.sleep(min_interval_s)
    return int(min_interval_s * 1000)


def sleep(seconds):
    """Backoff wait. Returns ms, for accumulation into queue_wait_ms — backoff
    is never folded into latency_ms (§2)."""
    time.sleep(seconds)
    return int(seconds * 1000)


def retry_after(error, attempt):
    header = error.headers.get("Retry-After", "")
    if header.strip().isdigit():
        return int(header)
    return BACKOFF_S[attempt]


def failure(error_raw, http_status, failure_code, started, queue_wait_ms, retry_count):
    return CallResult(
        response_text="", finish_reason="", tokens_in=0, tokens_out=0,
        tokens_estimated=False, http_status=http_status, model_version="",
        latency_ms=int((time.monotonic() - started) * 1000),
        time_to_first_token_ms=0, queue_wait_ms=queue_wait_ms,
        status="failure", failure_code=failure_code, error_raw=error_raw,
        retry_count=retry_count,
    )

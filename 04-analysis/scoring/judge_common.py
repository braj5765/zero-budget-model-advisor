"""Shared judge-prompt construction and OpenRouter transport, used by both
judge.py (20-item calibration) and judge_production.py (400+80-item production
pass). Extracted here because both need the identical prompt content byte for
byte -- copying it a second time is how judge_prompt.md and judge.py's
DIMENSIONS/ANCHORS already drifted once (constraint_conformance vs
enum_constraint_conformance, aliased in agreement.py). One file, one place to
keep the two runners' judge identical.

Judge model and terms: 00-planning/ToS-Review.md S5.1/S5.1b.
Prompt version: judge_prompt.md v1.3 (adds {{PROBES}}; see its changelog).
"""

import http.client
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1].parent
CASES = ROOT / "01-rubric-and-testcases" / "cases"
RUN_FILE = ROOT / "03-results" / "run-2026-08-15T114622Z.jsonl"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# minimax/minimax-m3:free via GMICloud -- the judge that cleared the kappa
# gate (0.650, ToS-Review.md S5.1b, JUDGE-RUN-PLAN.md S4b). Routing pinned to
# this one verified provider rather than left to OpenRouter's default
# selection, so "the judge" is one verifiable thing across every call.
JUDGE_MODEL = "minimax/minimax-m3:free"
JUDGE_MODEL_PINNED_SLUG = "minimax/minimax-m3-20260531"
JUDGE_PROVIDER = "GMICloud"
PROMPT_VERSION = "1.3"

SCALE = """Every dimension is scored 0-3. Four points, no midpoint.
3 - Fully correct. A competent practitioner would ship this unchanged.
2 - Correct in substance, minor flaw. Usable after a trivial edit.
1 - Materially flawed. Contains an error a user would have to catch and fix.
0 - Unusable or wrong in a way that would mislead the user."""

NA_RULE = """A dimension may be marked n/a only where the case design makes it unscoreable, and the
case's scoring notes must say which dimensions are n/a and why. A judge may never mark
n/a at its own discretion."""

OUTPUT = """OUTPUT
Return a JSON object and nothing else:
{"scores": {"<dimension>": <0|1|2|3|"n/a">, ...},
 "justifications": {"<dimension>": "<one sentence>", ...}}
Use the exact dimension names given above, lowercased, spaces as underscores."""

TASK_FILES = {
    "summarization": "summarization.json",
    "extraction": "extraction.json",
    "classification": "classification.json",
    "rag-qa": "rag-qa.json",
    "json-output": "json-output.json",
}

DIMENSIONS = {
    "summarization": """faithfulness  - 3: every claim traceable to the source; nothing invented.
                0: contains a claim contradicted by or absent from the source.
coverage      - 3: captures all key points identified in the gold reference.
                0: misses the primary point of the source.
concision     - 3: within the requested length; no padding or restatement.
                0: substantially over length, or mostly filler.
instruction_adherence - 3: honours format, length, tone and audience as instructed.
                0: ignores the instruction.""",
    "extraction": """precision     - 3: no extracted field is wrong or hallucinated.
                0: majority of fields wrong or fabricated.
recall        - 3: all fields present in the source were extracted.
                0: most present fields missed.
normalisation - 3: dates, numbers, units, names in the requested canonical form.
                0: raw or inconsistent forms throughout.
null_handling - 3: absent fields returned as null, AND determinable fields resolved
                   rather than nulled.
                0: fabricates plausible values for absent fields, or nulls fields the
                   source does determine.""",
    "classification": """label_correctness  - 3: matches the gold label.  0: wrong label.
label_validity     - 3: output is a member of the permitted label set.
                     0: invents a label outside the set.
ambiguity_handling - 3: on deliberately ambiguous cases, flags or picks the defensible
                        label.
                     0: picks confidently and wrongly with no signal of uncertainty.""",
    "rag-qa": """groundedness      - 3: every assertion supported by the supplied context.
                    0: asserts facts not in the context.
answer_correctness- 3: factually answers the question asked.  0: wrong answer.
abstention_calibration - First decide which branch this case is in, from the gold
                       answer alone: UNANSWERABLE (gold answer is INSUFFICIENT
                       CONTEXT) or ANSWERABLE (gold gives a real answer).
                       If UNANSWERABLE: 3 if the response states INSUFFICIENT
                       CONTEXT, 0 if it answers anyway.
                       If ANSWERABLE: 3 if the response gives the answer, 0 if it
                       states INSUFFICIENT CONTEXT instead of answering.
                       Score only the branch that applies to this case. Answering
                       an ANSWERABLE question correctly is the 3 case, never a
                       deduction - do not score this dimension by checking whether
                       the response used the INSUFFICIENT CONTEXT token in
                       isolation from whether this case needed it.
citation_accuracy - 3: points to the passage that actually supports the claim.
                    0: cites a passage that does not support it.""",
    "json-output": """parseability   - 3: parses on first attempt, no wrapper prose or fences.
                 0: fails to parse.
schema_conformance - 3: all required keys present, types correct, no extra keys.
                 0: violates the schema.
constraint_conformance - 3: constrained/enum values respected.
                 0: values outside the permitted set.
content_correctness - 3: values are factually right.  0: values wrong.""",
}

ANCHORS = {
    "summarization": """COVERAGE ANCHOR
Coverage is judged by significance and against the length the instruction permits - never
by counting gold points. If the point the case was designed to probe (its probes field, or
the point named in gold.notes) is missed, coverage caps at 1 however many other points
landed. If the probed point lands, coverage is 3 where the omitted points are ones the
requested length could not accommodate, and 2 where the summary had room and still dropped
a substantive point. The length clause is load-bearing: a three-sentence summary cannot
carry five gold points, and marking it down for obeying the length instruction
double-counts the same behaviour against instruction adherence, which is its own dimension.""",
    "extraction": """PRECISION ANCHOR
Precision scores whether the value is correct, not how it is worded. A semantically
equivalent rewording of the correct value scores 3. A value carrying content the gold does
not contain scores 2 - the field is not the requested value and a consumer must edit it -
or lower where that content is not in the source at all, which is fabrication. Differences
of canonical form (date format, unit, casing, separators) are normalisation's business,
not precision's, and must not be charged twice.

NULL HANDLING ANCHOR
Over-abstention is scored here too, and symmetrically. Fabrication scores 0; nulling a
determinable value scores 1. Inventing a value misleads silently, while over-nulling
merely under-delivers.""",
    "classification": """The classification label is the first line of the response, and only the first line.
Check label_correctness and label_validity against that line alone. Any second line
beginning "Note:" is a separate, optional channel for uncertainty (see ambiguity
handling below) - it is never itself the label, must not be read as an alternate
answer, and its content must not be checked against the permitted label set.

The permitted label set is stated in the instruction. Any string outside it is a
label-validity failure scored 0 however reasonable the reading - this is the
integration-breaking failure the rubric separates from correctness. The optional
"Note:" line is the sanctioned channel for uncertainty; using it where no genuine
ambiguity exists costs a point on ambiguity handling.""",
    "rag-qa": """Abstention is symmetric. A model that abstains on answerable questions is not being
careful; it would otherwise game this dimension by refusing everything. Check the gold
answer's branch (dimensions block above) before scoring abstention_calibration - never
penalise a response for answering when the gold answer itself is not INSUFFICIENT
CONTEXT. The sanctioned abstention token is INSUFFICIENT CONTEXT, and citations appear
on a final "Citations:" line. Where the supporting-passage list is empty, no answer
should have been given and citing anything is a citation failure.""",
    "json-output": """Parseability is scored before content. Markdown fences around an otherwise perfect object
are a parseability failure, not a formatting quibble - the response as delivered does not
parse. If the response is unparseable, score parseability 0 and mark the content
dimensions n/a per the not-applicable rule, so the failure is attributed to the right
dimension rather than double-counted.""",
}

TEMPLATE = """You are scoring one model response against a fixed rubric. You are not the author of the
response and you do not know which model produced it. Score only what is in front of you.

SCALE
{scale}

DIMENSIONS FOR THIS TASK
{dimensions}

{anchors}

NOT-APPLICABLE RULE
{na_rule}

WHAT YOU ARE SCORING
Task: {task}
Instruction given to the model:
{instruction}

Source material provided to the model:
{source}

Gold reference / expected answer:
{gold}

What this case was designed to probe:
{probes}

Scoring notes for this case (authoritative where they conflict with your own reading):
{gold_notes}

Model response - RAW AND UNMODIFIED. Markdown fences, prose wrappers, leading or trailing
text are part of the response and must be scored as such. Do not mentally clean it up.
<<<RESPONSE
{response_text}
RESPONSE>>>

RULES
1. Score every dimension listed above, in the order listed.
2. Use only 0, 1, 2, 3 - or "n/a" where and only where the scoring notes above say the
   dimension is unscoreable for this case. You may never decide a dimension is n/a
   yourself.
3. Give exactly one sentence of justification per dimension, naming the specific thing in
   the response that decided the score. "Good summary" is not a justification.
4. Judge the response as delivered, not the response you would have written.
5. Do not reward or penalise length, tone, or confidence except where a dimension says to.

{output}"""


def format_gold(task, gold):
    if task == "summarization":
        return (
            f"must_include: {gold.get('must_include')}\n"
            f"must_not_include: {gold.get('must_not_include')}\n"
            f"reference: {gold.get('reference')}"
        )
    if task == "rag-qa":
        return (
            f"answer: {gold.get('answer')}\n"
            f"supported_by: {gold.get('supported_by')}\n"
            f"must_include: {gold.get('must_include')}\n"
            f"must_not_include: {gold.get('must_not_include')}\n"
            f"reference: {gold.get('reference')}"
        )
    return json.dumps(gold.get("expected"), indent=2)


def load_cases():
    cases = {}
    for task, fname in TASK_FILES.items():
        with open(CASES / fname, encoding="utf-8") as f:
            data = json.load(f)
        for c in data["cases"]:
            cases[c["case_id"]] = c
    return cases


def load_run_rows():
    rows = []
    with open(RUN_FILE, encoding="utf-8") as f:
        for line in f:
            rows.append(json.loads(line))
    return rows


def build_prompt(task, case, response_text):
    return TEMPLATE.format(
        scale=SCALE,
        dimensions=DIMENSIONS[task],
        anchors=ANCHORS[task],
        na_rule=NA_RULE,
        task=task,
        instruction=case["instruction"],
        source=case.get("source", ""),
        gold=format_gold(task, case["gold"]),
        probes=case["probes"],
        gold_notes=case["gold"].get("notes", ""),
        response_text=response_text,
        output=OUTPUT,
    )


def load_dotenv(env_path):
    """Same seven lines as 02-harness/runner.py's _load_env, duplicated rather
    than imported: /scoring does not depend on /harness (PROJECT-STATE S4b.1)."""
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            name, value = line.split("=", 1)
            os.environ.setdefault(name.strip(), value.strip().strip('"').strip("'"))


MAX_RATE_LIMIT_RETRIES = 5

# Unconditional pre-call delay, same semantics as 02-harness/clients/base.py's
# pace() (not imported -- /scoring does not depend on /harness, PROJECT-STATE
# S4b.1 -- but the approach is deliberately identical: a flat sleep, not a
# token bucket). Raised from 0 to 5s after the production pass measured a
# sustained ~26% failure rate (mostly RATE_LIMIT) at the unpaced rate that had
# been clean at 20 rows -- the shared pool's limit is on request rate, not
# raw per-call latency, and a burst of small/fast calls (e.g. classification)
# hits it even though the observed mean call time looks fine. Tune upward
# again if the resumed pass still shows a sustained (not just occasional)
# RATE_LIMIT rate; prefer slow over lost calls.
MIN_INTERVAL_S = 5.0


class JudgeCallFailure(Exception):
    """A genuine, non-retryable transport failure -- everything retryable
    (429, per client policy below) is already retried inside call_judge and
    never reaches the caller as an exception. Carries a rubric S6-style code
    so failure rows are countable the same way the harness's own failure
    taxonomy is."""

    def __init__(self, code, detail):
        self.code = code
        self.detail = detail
        super().__init__(f"{code}: {detail}")


def call_judge(prompt):
    """Single shot on the judge's actual reply -- JUDGE-RUN-PLAN S4b: a judge
    call failure is an instrumentation failure, not a finding about a
    benchmarked model, so (unlike the harness's own no-retry-on-failure rule)
    it IS retried -- on the next resume, as a fresh appended row, never in
    place. A 429 is transport availability, not a judge failure -- retried a
    bounded number of times within this call, honouring the provider's own
    Retry-After; only once that budget is exhausted does it become a
    RATE_LIMIT JudgeCallFailure for this attempt. Provider routing is pinned
    to JUDGE_PROVIDER; the caller checks the returned provider against it
    (identity guard, JUDGE-RUN-PLAN S1/production)."""
    time.sleep(MIN_INTERVAL_S)
    api_key = os.environ["OPENROUTER_API_KEY"]
    body = json.dumps({
        "model": JUDGE_MODEL,
        "provider": {"only": [JUDGE_PROVIDER]},
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "stream": False,
        "response_format": {"type": "json_object"},
    }).encode("utf-8")
    req = urllib.request.Request(
        OPENROUTER_URL, data=body,
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + api_key},
    )
    for attempt in range(MAX_RATE_LIMIT_RETRIES + 1):
        try:
            with urllib.request.urlopen(req, timeout=180) as resp:
                raw_body = resp.read()
            try:
                outer = json.loads(raw_body)
            except json.JSONDecodeError as error:
                # A 200 whose body isn't valid JSON at all (truncated stream,
                # an HTML error page) -- same non-retryable bucket as any
                # other response shape the API contract doesn't guarantee.
                raise JudgeCallFailure(
                    "API_ERROR", f"non-JSON response body: {raw_body[:300]!r}") from error
            try:
                content = outer["choices"][0]["message"]["content"]
            except (KeyError, IndexError, TypeError) as error:
                # A 200 with no usable choices (moderation, upstream oddity) is
                # not retryable by this policy -- same bucket as any other
                # response shape the API contract doesn't promise to fix itself.
                raise JudgeCallFailure("API_ERROR", f"malformed response body: {outer}") from error
            return content, outer.get("model", ""), outer.get("provider", "")
        except urllib.error.HTTPError as error:
            error_body = error.read().decode(errors="replace")
            if error.code == 429 and attempt < MAX_RATE_LIMIT_RETRIES:
                retry_after = int(error.headers.get("Retry-After", 5))
                try:
                    retry_after = json.loads(error_body)["error"]["metadata"].get(
                        "retry_after_seconds", retry_after)
                except (KeyError, ValueError, TypeError):
                    pass
                print(f"  429 upstream_provider_shared_pool, retrying in {retry_after}s "
                      f"(attempt {attempt + 1}/{MAX_RATE_LIMIT_RETRIES})")
                time.sleep(retry_after)
                continue
            if error.code == 429:
                raise JudgeCallFailure(
                    "RATE_LIMIT", f"exhausted {MAX_RATE_LIMIT_RETRIES} retries: {error_body}")
            raise JudgeCallFailure("API_ERROR", f"HTTP {error.code}: {error_body}")
        except TimeoutError:
            raise JudgeCallFailure("TIMEOUT", "no response within 180s")
        except urllib.error.URLError as error:
            raise JudgeCallFailure("API_ERROR", str(error.reason))
        except (http.client.HTTPException, ConnectionError) as error:
            # Covers IncompleteRead, RemoteDisconnected and similar transport
            # drops that are neither an HTTPError nor a URLError -- observed
            # in production as a chunked response cut off mid-stream.
            raise JudgeCallFailure("API_ERROR", f"{type(error).__name__}: {error}") from error


def parse_judge_output(raw):
    text = raw.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text.strip())


JSON_OUTPUT_CONTENT_DIMS = {
    "schema_conformance", "constraint_conformance", "enum_constraint_conformance",
    "content_correctness",
}


def na_eligible_dimensions(task, case, response_text):
    """Rubric S3.6 rule 1: n/a is sanctioned only by case design, never by judge
    discretion. The two design-level cases in the case files: a classification
    case with no correct label (gold.expected is null, gold.expected_any given
    instead -- cls-a02 is the only instance), and an unparseable json-output
    response (S3.5 -- content dimensions have nothing to judge)."""
    eligible = set()
    if task == "classification" and case["gold"].get("expected") is None \
            and "expected_any" in case["gold"]:
        eligible.add("label_correctness")
    if task == "json-output":
        try:
            json.loads(response_text)
        except json.JSONDecodeError:
            eligible |= JSON_OUTPUT_CONTENT_DIMS
    return eligible

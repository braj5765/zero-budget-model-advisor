"""Production judge pass -- rubric v1.6 S4b (median-of-three restored, reverting
v1.5's run_index=1-plus-subsample reduction once the hosted judge measured
4.4s/row rather than the 6min/row the reduction was based on).

Work list: 04-analysis/production/manifest.json's 400 (case_id, model_id)
pairs x all 3 run_indices -- 1,200 distinct rows total.

Resumable, append-only JSONL (JUDGE-RUN-PLAN S2/S4b): one line per attempt,
flushed immediately. Resume key (case_id, model_id, run_index), but unlike
the harness's own no-retry-on-failure rule, a row is only "done" (skipped on
resume) if its *latest* row for that key has status=="success" -- a
RATE_LIMIT/API_ERROR/MALFORMED row is re-attempted, appending a fresh row,
never edited in place. This is deliberate and recorded in JUDGE-RUN-PLAN S4b:
a judge call failure is an instrumentation failure, not a finding about the
benchmarked model being judged, so laundering it away by retrying (which is
exactly what the harness must never do for a *model's* response) is correct
here. /scoring must therefore read the latest row per key, matching the
existing convention for probe.jsonl. --minutes N spends a time budget and
exits cleanly after finishing the item in flight; --limit N stops after N
new rows regardless of time. Run identity: explicit --run-id wins, --new-run
forces a fresh one, default resumes the most recent file in
04-analysis/production/.

Judge identity guard: every row records judge_model, judge_model_pinned_slug,
judge_provider_requested/returned, prompt and rubric version, and an
ISO-8601 timestamp. Provider routing is pinned (judge_common.call_judge's
provider.only); if OpenRouter ever returns a provider other than the pinned
one anyway, the run halts immediately -- rubric S5 requires one pinned judge
per index release.

Failure handling: a 429 is retried with backoff inside call_judge (with a
judge_common.MIN_INTERVAL_S pre-call pace on top, raised after this pass
measured a sustained ~26% failure rate at the unpaced call rate) and never
reaches here unless that budget is exhausted -- it is transport availability,
not a judge failure, so it is never recorded as one on its own. Only a
genuine per-attempt failure (JudgeCallFailure from call_judge, or the judge's
own reply failing to parse) gets a failure row: status="failed" with a
rubric S6-style failure_code (RATE_LIMIT, TIMEOUT, API_ERROR, MALFORMED).

No prompt or rubric changes during this pass, by policy (not enforced in
code): if either must change, the pass restarts under a new --run-id.
judge_prompt.md stays v1.3, Scoring-Rubric.md stays v1.6, for the entire pass.
"""

import argparse
import datetime
import json
import sys
import time

from judge_common import (
    JUDGE_MODEL, JUDGE_MODEL_PINNED_SLUG, JUDGE_PROVIDER, PROMPT_VERSION,
    ROOT, JudgeCallFailure, build_prompt, call_judge, load_cases, load_dotenv,
    load_run_rows, na_eligible_dimensions, parse_judge_output,
)

RUBRIC_VERSION = "1.6"
PRODUCTION_DIR = ROOT / "04-analysis" / "production"
MANIFEST_FILE = PRODUCTION_DIR / "manifest.json"
RUN_INDICES = (1, 2, 3)


def load_manifest():
    with open(MANIFEST_FILE, encoding="utf-8") as f:
        return json.load(f)


def build_work_list(manifest):
    return [
        (p["case_id"], p["model_id"], run_index, p["task"])
        for p in manifest["eligible_pairs"]
        for run_index in RUN_INDICES
    ]


def index_run_rows(rows):
    by_key = {}
    for r in rows:
        key = (r["case_id"], r["model_id"], r["run_index"])
        if r.get("provider") != "openrouter" and r["status"] == "success":
            by_key[key] = r
    return by_key


def resolve_run_file(run_id, new_run):
    PRODUCTION_DIR.mkdir(exist_ok=True)
    if run_id:
        return PRODUCTION_DIR / f"judge-run-{run_id}.jsonl"
    if new_run:
        run_id = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        return PRODUCTION_DIR / f"judge-run-{run_id}.jsonl"
    existing = sorted(PRODUCTION_DIR.glob("judge-run-*.jsonl"))
    if existing:
        return existing[-1]
    run_id = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return PRODUCTION_DIR / f"judge-run-{run_id}.jsonl"


# Rows written before this fix used "judged" for a successful attempt (the
# label was renamed to "success" to match the instruction's exact wording);
# historical rows are read, not rewritten -- JSONL here is append-only, and
# the label change carries no semantic difference worth a rewrite.
SUCCESS_STATUSES = {"success", "judged"}


def load_latest_status(out_file):
    """Latest row per key wins -- a key can appear more than once now that
    failures are retried by appending, not edited in place."""
    latest = {}
    if not out_file.exists():
        return latest
    with open(out_file, encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)
            latest[(row["case_id"], row["model_id"], row["run_index"])] = row["status"]
    return latest


def now_iso():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def judge_one(case, task, response_text):
    """Returns a dict ready to merge with identity/timing fields. Never
    raises for a judge-side failure -- only a provider-identity mismatch is
    signalled separately (checked by the caller, since it's a run-level
    halt, not a per-row failure)."""
    prompt = build_prompt(task, case, response_text)
    try:
        raw, returned_model, returned_provider = call_judge(prompt)
    except JudgeCallFailure as error:
        return {"status": "failed", "failure_code": error.code, "error": error.detail,
                "judge_model_returned": "", "judge_provider_returned": ""}, None

    try:
        parsed = parse_judge_output(raw)
    except (json.JSONDecodeError, KeyError) as error:
        return {
            "status": "failed", "failure_code": "MALFORMED", "error": str(error),
            "raw_response": raw, "judge_model_returned": returned_model,
            "judge_provider_returned": returned_provider,
        }, returned_provider

    eligible = na_eligible_dimensions(task, case, response_text)
    na_protocol_violations = [
        dim for dim, val in parsed["scores"].items() if val == "n/a" and dim not in eligible
    ]
    return {
        "status": "success", "scores": parsed["scores"], "justifications": parsed["justifications"],
        "na_protocol_violations": na_protocol_violations,
        "judge_model_returned": returned_model, "judge_provider_returned": returned_provider,
    }, returned_provider


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--minutes", type=float, default=None,
                     help="Time budget; finish the in-flight item, then exit.")
    ap.add_argument("--limit", type=int, default=None,
                     help="Stop after this many new rows, regardless of time.")
    ap.add_argument("--run-id", type=str, default=None, help="Resume this exact run id.")
    ap.add_argument("--new-run", action="store_true", help="Force a fresh run id.")
    args = ap.parse_args()

    load_dotenv(ROOT / ".env")
    manifest = load_manifest()
    work_list = build_work_list(manifest)
    cases = load_cases()
    rows_by_key = index_run_rows(load_run_rows())

    out_file = resolve_run_file(args.run_id, args.new_run)
    latest_status = load_latest_status(out_file)
    succeeded_keys = {k for k, s in latest_status.items() if s in SUCCESS_STATUSES}
    remaining = [w for w in work_list if (w[0], w[1], w[2]) not in succeeded_keys]
    n_retries_pending = sum(1 for w in remaining if (w[0], w[1], w[2]) in latest_status)

    print(f"run file: {out_file.name}")
    print(f"work list: {len(work_list)} total, {len(succeeded_keys)} succeeded, "
          f"{len(remaining)} remaining ({n_retries_pending} of those are retries of a prior failure)")
    if args.minutes:
        print(f"budget: {args.minutes} minutes")
    if args.limit:
        print(f"limit: {args.limit} new rows")

    started = time.monotonic()
    n_done_this_run = 0
    n_failed_this_run = 0
    n_retried_this_run = 0

    with open(out_file, "a", encoding="utf-8") as sink:
        for case_id, model_id, run_index, task in remaining:
            if args.limit is not None and n_done_this_run >= args.limit:
                print(f"limit of {args.limit} reached, stopping")
                break
            if args.minutes is not None and (time.monotonic() - started) / 60 >= args.minutes:
                print(f"budget of {args.minutes} minutes spent, stopping")
                break

            key = (case_id, model_id, run_index)
            is_retry = key in latest_status
            case = cases[case_id]
            row = rows_by_key[key]

            call_started = time.monotonic()
            result, returned_provider = judge_one(case, task, row["response_text"])
            call_elapsed = time.monotonic() - call_started

            if returned_provider and returned_provider != JUDGE_PROVIDER:
                sink.flush()
                sys.exit(
                    f"HALT: {case_id}/{model_id}/run{run_index} served by "
                    f"{returned_provider!r}, expected {JUDGE_PROVIDER!r}. A different "
                    f"upstream provider may be a differently quantized model -- rubric "
                    f"S5 requires one pinned judge per index release. Run halted; "
                    f"{n_done_this_run} rows written this session, resumable."
                )

            record = {"case_id": case_id, "model_id": model_id, "run_index": run_index, "task": task}
            if is_retry:
                record["retry_of_failed_attempt"] = True
            record.update(result)
            record.update({
                "judge_model": JUDGE_MODEL,
                "judge_model_pinned_slug": JUDGE_MODEL_PINNED_SLUG,
                "judge_provider_requested": JUDGE_PROVIDER,
                "judge_prompt_version": PROMPT_VERSION,
                "rubric_version": RUBRIC_VERSION,
                "timestamp": now_iso(),
                "call_seconds": round(call_elapsed, 1),
            })
            sink.write(json.dumps(record, ensure_ascii=False) + "\n")
            sink.flush()

            n_done_this_run += 1
            if is_retry:
                n_retried_this_run += 1
            if record["status"] == "failed":
                n_failed_this_run += 1
                flag = f"  [FAILED: {record['failure_code']}]"
            else:
                flag = "  [retry succeeded]" if is_retry else ""
            print(f"[{n_done_this_run}] {case_id}/{model_id}/run{run_index} "
                  f"({call_elapsed:.1f}s){flag}")

    elapsed_min = (time.monotonic() - started) / 60
    print(f"\n{n_done_this_run} attempts this session ({n_failed_this_run} failed, "
          f"{n_retried_this_run} were retries of a prior failure) in {elapsed_min:.1f} min"
          + (f" ({elapsed_min * 60 / n_done_this_run:.1f}s/attempt)" if n_done_this_run else ""))
    total_succeeded = len(succeeded_keys) + (n_done_this_run - n_failed_this_run)
    print(f"total: {total_succeeded}/{len(work_list)} succeeded, "
          f"{len(work_list) - total_succeeded} remaining")


if __name__ == "__main__":
    main()

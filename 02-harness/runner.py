"""Matrix execution, resumability, record writing (Harness-Spec §1, §2, §4).

Contains no provider names: clients are resolved from the `provider` string in
config. If a provider name ever appears in this file, the abstraction has
failed (§6).
"""

import argparse
import datetime
import importlib
import json
import os
import pathlib
import subprocess
import sys
import tomllib
import uuid

import clients.base

HARNESS_VERSION = "1.0"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="02-harness/config.toml")
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--run-id")
    parser.add_argument("--new-run", action="store_true")
    args = parser.parse_args()

    config = tomllib.load(open(args.config, "rb"))
    _load_env(pathlib.Path(".env"))
    _preflight(config)
    cases = _load_cases(pathlib.Path(config["paths"]["cases_dir"]))

    results_dir = pathlib.Path(config["paths"]["results_dir"])
    results_dir.mkdir(parents=True, exist_ok=True)
    run_id = _resolve_run_id(results_dir, args.run_id, args.new_run)
    results_path = results_dir / ("run-%s.jsonl" % run_id)
    done = _already_done(results_path)

    total = len(config["models"]) * len(cases) * args.runs
    print("run_id %s · %d complete · %d remaining" % (run_id, len(done), total - len(done)))

    git_commit = _git_commit()
    if not git_commit:
        print("WARNING: git provenance unresolved — records will carry an empty "
              "git_commit and cannot be tied to the code that produced them")
    # Sequenced per provider rather than parallel: parallelism against a free
    # tier only buys 429s faster (§1).
    with open(results_path, "a", encoding="utf-8") as sink:
        for model in config["models"]:
            client = importlib.import_module("clients." + model["provider"])
            params = {**config["params"], **model}
            for case in cases:
                prompt = _build_prompt(case)
                for run_index in range(1, args.runs + 1):
                    key = [case["case_id"], model["id"], run_index]
                    if key in done:
                        continue
                    result = client.call(prompt, params["system_prompt"], params)
                    record = _record(case, model, params, prompt, run_index,
                                     result, run_id, git_commit)
                    sink.write(json.dumps(record, ensure_ascii=False) + "\n")
                    # Flushed per line so a kill mid-run loses at most the
                    # in-flight call, never a completed one (§4).
                    sink.flush()


def _load_env(env_path):
    """Load .env into the environment. Keys live there, never in config, which
    is committed. Seven lines of stdlib rather than a runtime dependency."""
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            name, value = line.split("=", 1)
            os.environ.setdefault(name.strip(), value.strip().strip('"').strip("'"))


def _preflight(config):
    """Gate, not error handling: verify every key is present and accepted before
    spending quota on the matrix.

    A missing or rejected key would otherwise be recorded as ~300 API_ERROR
    rows and published as a finding about the provider, when it is a finding
    about the setup. Five calls to prevent that is a trade worth making.
    """
    missing = [m["api_key_env"] for m in config["models"]
               if m.get("api_key_env") and not os.environ.get(m["api_key_env"])]
    if missing:
        sys.exit("preflight: missing key(s) in environment or .env: " + ", ".join(missing))

    for model in config["models"]:
        client = importlib.import_module("clients." + model["provider"])
        params = {**config["params"], **model, "max_tokens": 8}
        result = client.call("ping", "", params)
        if result.http_status in (401, 403) or result.failure_code == "API_ERROR":
            sys.exit("preflight: %s rejected the call (HTTP %s): %s"
                     % (model["id"], result.http_status, result.error_raw[:300]))
        print("preflight ok · %s · %s" % (model["id"], result.model_version or "no version reported"))


def _load_cases(cases_dir):
    cases = []
    for path in sorted(cases_dir.glob("*.json")):
        payload = json.load(open(path, encoding="utf-8"))
        for case in payload["cases"]:
            # `task` lives at file level; carried onto each case for §2 identity.
            cases.append({**case, "task": payload["task"]})
    return cases


def _build_prompt(case):
    """Append `source` only when its full text is absent from `instruction`.

    Case files disagree: classification, json-output and rag-qa restate the
    source inside the instruction, summarization and extraction do not. The
    match is on the entire source string, so a partial overlap appends rather
    than half-matching.
    """
    source = case.get("source", "")
    if source and source not in case["instruction"]:
        return case["instruction"] + "\n\n" + source
    return case["instruction"]


def _already_done(results_path):
    """Every (case_id, model_id, run_index) already written to this run."""
    if not results_path.exists():
        return []
    done = []
    for line in open(results_path, encoding="utf-8"):
        if line.strip():
            record = json.loads(line)
            done.append([record["case_id"], record["model_id"], record["run_index"]])
    return done


def _record(case, model, params, prompt, run_index, result, run_id, git_commit):
    return {
        "call_id": str(uuid.uuid4()),
        "case_id": case["case_id"],
        "task": case["task"],
        "difficulty": case["difficulty"],
        "model_id": model["id"],
        "provider": model["provider"],
        "model_version": result.model_version,
        "run_index": run_index,
        "prompt": prompt,
        "system_prompt": params["system_prompt"],
        "temperature": params["temperature"],
        "max_tokens": params["max_tokens"],
        # Effective retry policy for this call. Standard unless overridden;
        # recorded so an accidental override is visible in the raw data.
        "retry_attempts_allowed": clients.base.attempts_allowed(params),
        "timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "response_text": result.response_text,
        "finish_reason": result.finish_reason,
        "tokens_in": result.tokens_in,
        "tokens_out": result.tokens_out,
        "tokens_estimated": result.tokens_estimated,
        "http_status": result.http_status,
        "latency_ms": result.latency_ms,
        "time_to_first_token_ms": result.time_to_first_token_ms,
        "queue_wait_ms": result.queue_wait_ms,
        "status": result.status,
        "failure_code": result.failure_code,
        "error_raw": result.error_raw,
        "retry_count": result.retry_count,
        "run_id": run_id,
        "harness_version": HARNESS_VERSION,
        "git_commit": git_commit,
    }


def _resolve_run_id(results_dir, explicit, new_run):
    """Explicit wins, --new-run forces fresh, otherwise resume the most recent
    existing run file (Harness-Spec §4).

    Resuming is the default because the asymmetry is severe: a wrong resume
    costs one suppressed duplicate, a wrong fresh start costs ~1,500 calls of
    free-tier quota. A run spanning days is the expected case, so a
    date-derived default would re-execute completed work every midnight.
    """
    if explicit:
        return explicit
    existing = sorted(results_dir.glob("run-*.jsonl"), key=lambda p: p.stat().st_mtime)
    if existing and not new_run:
        return existing[-1].name[len("run-"):-len(".jsonl")]
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")


def _git_commit():
    """`--dirty` is the load-bearing half: a bare hash recorded while the tree
    had uncommitted changes points at code that never existed in any commit."""
    return subprocess.run(["git", "describe", "--always", "--dirty"],
                          capture_output=True, text=True).stdout.strip()


if __name__ == "__main__":
    main()

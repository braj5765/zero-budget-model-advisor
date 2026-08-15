"""Rate-limit probing mode (Harness-Spec §5).

Run after the main benchmark, never before and never concurrently. Measures the
ceiling the docs don't state, then stops.

Probing is gated on `probe_allowed` in config, per provider. That flag is the
whole gate: no provider is named here, so a provider whose terms forbid probing
is excluded by data rather than by a special case in code — a hardcoded
exception is exactly the kind of thing that survives a refactor and quietly
probes a forbidden provider next quarter (ToS-Review R-1).
"""

import argparse
import datetime
import importlib
import json
import pathlib
import time
import tomllib

import runner
from clients import base

PROMPT = "Reply with the single word: ok"
SUSTAINED = 2          # consecutive rejections that count as a real ceiling
MAX_REQUESTS = 200     # backstop; probing stops at the ceiling long before this
REPROBE_HOURS = 24


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="02-harness/config.toml")
    args = parser.parse_args()

    config = tomllib.load(open(args.config, "rb"))
    runner._load_env(pathlib.Path(".env"))
    out_path = pathlib.Path(config["paths"]["results_dir"]) / "probe.jsonl"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    recent = _recently_probed(out_path)

    for model in config["models"]:
        if not model.get("probe_allowed"):
            # Ceiling still gets published — from the documented figure, plus
            # any rejections seen incidentally during the benchmark run.
            print("skip %s · probing not permitted · provenance: documented + incidental"
                  % model["id"])
            continue
        if model["id"] in recent:
            print("skip %s · probed within %dh" % (model["id"], REPROBE_HOURS))
            continue
        record = _probe(model, config)
        with open(out_path, "a", encoding="utf-8") as sink:
            sink.write(json.dumps(record, ensure_ascii=False) + "\n")
        print("%s · %d requests before first rejection · %.1f rpm at rejection · %s"
              % (model["id"], record["requests_before_first_rejection"],
                 record["rpm_at_rejection"], record["limit_period_guess"]))


def _probe(model, config):
    """Slowly increasing rate until the first sustained limit, then stop.

    Does not characterise the recovery curve and does not probe again for 24
    hours. The point is the ceiling, not a load test (§5).
    """
    client = importlib.import_module("clients." + model["provider"])
    # Probe unpaced: the config floor exists to stay under the ceiling, which is
    # the thing being measured here.
    params = {**config["params"], **model, "max_tokens": 8, "min_interval_s": 0.0}

    interval = 60.0 / max(model.get("documented_rpm") or 1, 1)
    sent = 0
    first_rejection_at = 0
    consecutive = 0
    rpm_at_rejection = 0.0
    error_raw = ""
    started = time.monotonic()

    while sent < MAX_REQUESTS:
        result = client.call(PROMPT, "", params)
        sent += 1
        if result.failure_code == base.RATE_LIMIT:
            consecutive += 1
            if not first_rejection_at:
                first_rejection_at = sent
                elapsed = max(time.monotonic() - started, 1e-6)
                rpm_at_rejection = sent / elapsed * 60
                error_raw = result.error_raw
            if consecutive >= SUSTAINED:
                break
        else:
            consecutive = 0
            time.sleep(interval)
            interval = max(interval * 0.9, 0.05)   # slowly increase the rate

    return {
        "model_id": model["id"],
        "provider": model["provider"],
        "timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "requests_before_first_rejection": first_rejection_at or sent,
        "rpm_at_rejection": round(rpm_at_rejection, 1),
        "error_raw": error_raw,
        "limit_period_guess": _period(error_raw),
        "documented_rpm": model.get("documented_rpm", 0),
        "documented_rpd": model.get("documented_rpd", 0),
        "documented_source": model.get("documented_source", ""),
        "provenance": "measured",
        "harness_version": runner.HARNESS_VERSION,
        "git_commit": runner._git_commit(),
    }


def _period(error_raw):
    """Provisional read of whether the limit is per-minute, per-day or token
    based. Classified from the provider's own prose, which is stored verbatim
    above — audit and reclassify at analysis time rather than trusting this."""
    text = error_raw.lower()
    if "day" in text or "daily" in text or "rpd" in text:
        return "per-day"
    if "token" in text or "tpm" in text:
        return "token-based"
    if "minute" in text or "rpm" in text:
        return "per-minute"
    return "unknown"


def _recently_probed(out_path):
    if not out_path.exists():
        return set()
    cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=REPROBE_HOURS)
    recent = set()
    for line in out_path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            record = json.loads(line)
            if datetime.datetime.fromisoformat(record["timestamp_utc"]) > cutoff:
                recent.add(record["model_id"])
    return recent


if __name__ == "__main__":
    main()

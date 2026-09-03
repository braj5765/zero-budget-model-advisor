"""Judges the 20-item human calibration set with a hosted OpenRouter model.

Reads 04-analysis/calibration/sample.json (or --sample), resolves each item to
its byte-identical response in the run file (matched on case_id + run_index==1
+ response_sha256, never on the sealed map), builds the prompt per
04-analysis/scoring/judge_prompt.md v1.3 against Scoring-Rubric.md v1.4, and
writes 04-analysis/calibration/judge_scores_hosted_v1.3.json (or --out). All
prior runs (judge_scores.json, judge_scores_v1.2.json, judge_scores_hosted.json,
and any other --out) are untouched -- append-only, per JUDGE-RUN-PLAN.md.
--sample/--out/--rubric-version/--judged-at let the same script judge a
different named set (e.g. JUDGE-RUN-PLAN S6's held-out sample) without a
parallel copy of this file; the defaults reproduce the original 20-item
calibration run byte-for-byte. Shares prompt construction and transport with
judge_production.py via judge_common.py so the two runners' judge can never
silently drift apart.
"""

import argparse
import hashlib
import json
from pathlib import Path

from judge_common import (
    JUDGE_MODEL, JUDGE_MODEL_PINNED_SLUG, JUDGE_PROVIDER, PROMPT_VERSION,
    ROOT, build_prompt, call_judge, load_cases, load_dotenv, load_run_rows,
    na_eligible_dimensions, parse_judge_output,
)

CAL = ROOT / "04-analysis" / "calibration"


def find_response(rows, case_id, task, response_sha256):
    matches = [
        r for r in rows
        if r["case_id"] == case_id and r["task"] == task
        and r["run_index"] == 1 and r["status"] == "success"
        and hashlib.sha256(r["response_text"].encode("utf-8")).hexdigest() == response_sha256
    ]
    if not matches:
        raise ValueError(f"expected at least 1 eligible row for {case_id}, found 0")
    # Multiple models can produce byte-identical response_text (e.g. a trivial
    # correct JSON object) and therefore the same hash; since the text is
    # identical by construction, any match is equivalent for judging.
    return sorted(matches, key=lambda r: r["call_id"])[0]


def load_existing(out_file):
    if not out_file.exists():
        return {}, []
    with open(out_file, encoding="utf-8") as f:
        out = json.load(f)
    return {r["item_id"]: r for r in out["scores"]}, out["scores"]


def save(results, out_file, sample_name, rubric_version, judged_at):
    out = {
        "schema_version": "1.0",
        "judge_model": JUDGE_MODEL,
        "judge_model_pinned_slug": JUDGE_MODEL_PINNED_SLUG,
        "judge_provider": JUDGE_PROVIDER,
        "judge_prompt_version": PROMPT_VERSION,
        "rubric_version": rubric_version,
        "judged_at": judged_at,
        "sample": f"04-analysis/calibration/{sample_name}",
        "scores": results,
    }
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", default="sample.json", help="Filename under calibration/.")
    ap.add_argument("--out", default="judge_scores_hosted_v1.3.json",
                    help="Filename under calibration/ to write.")
    ap.add_argument("--rubric-version", default="1.4")
    ap.add_argument("--judged-at", default="2026-08-28")
    args = ap.parse_args()
    out_file = CAL / args.out

    load_dotenv(ROOT / ".env")
    with open(CAL / args.sample, encoding="utf-8") as f:
        sample = json.load(f)
    cases = load_cases()
    rows = load_run_rows()

    done_by_id, results = load_existing(out_file)
    if done_by_id:
        print(f"resuming: {len(done_by_id)} items already judged, skipping them")

    for item in sample["items"]:
        if item["item_id"] in done_by_id:
            continue

        case = cases[item["case_id"]]
        row = find_response(rows, item["case_id"], item["task"], item["response_sha256"])

        prompt = build_prompt(item["task"], case, row["response_text"])

        raw, returned_model, returned_provider = call_judge(prompt)
        parsed = parse_judge_output(raw)

        eligible = na_eligible_dimensions(item["task"], case, row["response_text"])
        na_protocol_violations = [
            dim for dim, val in parsed["scores"].items()
            if val == "n/a" and dim not in eligible
        ]

        results.append({
            "item_id": item["item_id"],
            "case_id": item["case_id"],
            "task": item["task"],
            "difficulty": item["difficulty"],
            "scores": parsed["scores"],
            "justifications": parsed["justifications"],
            "na_protocol_violations": na_protocol_violations,
            "judge_model": JUDGE_MODEL,
            "judge_model_pinned_slug": JUDGE_MODEL_PINNED_SLUG,
            "judge_model_returned": returned_model,
            "judge_provider_requested": JUDGE_PROVIDER,
            "judge_provider_returned": returned_provider,
            "judge_prompt_version": PROMPT_VERSION,
            "rubric_version": args.rubric_version,
        })
        if returned_provider and returned_provider != JUDGE_PROVIDER:
            print(f"WARNING: {item['item_id']} served by {returned_provider!r}, "
                  f"expected {JUDGE_PROVIDER!r}")
        print(f"{item['item_id']} ({item['case_id']}): {parsed['scores']}"
              + (f"  [NA VIOLATION: {na_protocol_violations}]" if na_protocol_violations else ""))
        save(results, out_file, args.sample, args.rubric_version, args.judged_at)

    print(f"\nWrote {len(results)} judged items to {out_file.name}")


if __name__ == "__main__":
    main()

"""Draws the held-out calibration sample for measuring whether kappa=0.650
generalises (PROJECT-STATE S2 item 1, JUDGE-RUN-PLAN S6). Same stratification
rule as calibration/sample.json -- one item per (task, model) cell, each task
exactly 1 hard case-slot and 3-of-5 tasks also 1 adversarial slot, each model
exactly 3 typical + 2 non-typical across its 5 task-slots -- applied to a
case_id pool that excludes every case_id already used in sample.json (not
just the (case, model) pairs), because the v1.2/v1.3 judge-prompt changes
were driven by those specific cases' content.

Writes calibration/sample_heldout.json (case identity + response hash, no
model identity -- same shape as sample.json) and
calibration/sealed_model_map_heldout.json (the model identity, sealed until
human_scores_heldout.json is complete -- same shape as sealed_model_map.json).
"""

import hashlib
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CASES = ROOT / "01-rubric-and-testcases" / "cases"
CAL = ROOT / "04-analysis" / "calibration"
RUN_FILE = ROOT / "03-results" / "run-2026-08-15T114622Z.jsonl"

SEED = 20260829
SOURCE_RUN = "03-results/run-2026-08-15T114622Z.jsonl"

TASK_FILES = {
    "summarization": "summarization.json",
    "extraction": "extraction.json",
    "classification": "classification.json",
    "rag-qa": "rag-qa.json",
    "json-output": "json-output.json",
}
MODELS = [
    "ollama-llama3.2-3b", "groq-llama-3.3-70b", "gemini-3.5-flash-lite", "mistral-small-2603",
]

# Fixed to match sample.json's own adversarial_tasks, not redrawn -- this is a
# matched comparison against one specific prior set, not a fresh representative
# sample of the case universe. summarization is the least-stable, worst-
# agreeing task across every calibration run (36-60% median-identical, 5 of 6
# v1.2 disagreements, cal-14 unresolved even in v1.3); json-output is the most
# stable. A held-out set that swapped summarization's adversarial slot for
# json-output's would be easier on exactly the slice the prompt was tuned
# against, biasing held-out kappa upward -- toward the reassuring result.
# See JUDGE-RUN-PLAN.md S6.
ADVERSARIAL_TASKS = {"extraction", "rag-qa", "summarization"}


def load_case_pool():
    pool = {}
    for task, fname in TASK_FILES.items():
        data = json.load(open(CASES / fname, encoding="utf-8"))
        for c in data["cases"]:
            pool[c["case_id"]] = (task, c["difficulty"])
    return pool


def excluded_case_ids():
    sample = json.load(open(CAL / "sample.json", encoding="utf-8"))
    return {item["case_id"] for item in sample["items"]}


def build_grid(rng):
    """5 tasks x 4 models -> difficulty label. Row constraint: 1 hard per
    task, ADVERSARIAL_TASKS also get 1 adversarial. Column constraint: each
    model exactly 2 non-typical slots total. Randomised construction, retried
    until the column constraint is met -- the search space is tiny (5
    tasks x 4 models) so this always terminates quickly in practice."""
    tasks = list(TASK_FILES)
    for _ in range(10000):
        capacity = {m: 2 for m in MODELS}
        order = tasks[:]
        rng.shuffle(order)
        grid = {}
        ok = True
        for task in order:
            needed = ["hard"] + (["adversarial"] if task in ADVERSARIAL_TASKS else [])
            available = [m for m in MODELS if capacity[m] > 0]
            if len(available) < len(needed):
                ok = False
                break
            chosen = rng.sample(available, len(needed))
            rng.shuffle(needed)
            row = {m: "typical" for m in MODELS}
            for m, diff in zip(chosen, needed):
                row[m] = diff
                capacity[m] -= 1
            grid[task] = row
        if ok and all(v == 0 for v in capacity.values()):
            return grid
    raise RuntimeError("could not build a balanced grid in 10000 attempts")


def main():
    rng = random.Random(SEED)
    case_pool = load_case_pool()
    excluded = excluded_case_ids()

    available_by_task_diff = {}
    for cid, (task, diff) in case_pool.items():
        if cid in excluded:
            continue
        available_by_task_diff.setdefault((task, diff), []).append(cid)
    n_available = sum(len(v) for v in available_by_task_diff.values())
    print(f"{len(excluded)} case_ids excluded (from sample.json); "
          f"{n_available} case_ids available for the held-out draw")

    grid = build_grid(rng)

    rows = [json.loads(l) for l in open(RUN_FILE, encoding="utf-8")]
    by_case_model = {
        (r["case_id"], r["model_id"]): r for r in rows
        if r["status"] == "success" and r["provider"] != "openrouter" and r["run_index"] == 1
    }

    drawn = []
    for task in TASK_FILES:
        needed = list(grid[task].values())
        picked = {}
        for diff in set(needed):
            pool = available_by_task_diff.get((task, diff), [])
            picked[diff] = rng.sample(pool, needed.count(diff))
        cursors = {d: 0 for d in picked}
        for model in MODELS:
            diff = grid[task][model]
            cid = picked[diff][cursors[diff]]
            cursors[diff] += 1
            row = by_case_model[(cid, model)]
            drawn.append({
                "case_id": cid,
                "task": task,
                "difficulty": diff,
                "model_id": model,
                "provider": row["provider"],
                "model_version": row["model_version"],
                "call_id": row["call_id"],
                "response_sha256": hashlib.sha256(row["response_text"].encode("utf-8")).hexdigest(),
            })

    rng.shuffle(drawn)
    for i, item in enumerate(drawn, 1):
        item["item_id"] = f"cal-h{i:02d}"

    difficulty_totals = {"typical": 0, "hard": 0, "adversarial": 0}
    for item in drawn:
        difficulty_totals[item["difficulty"]] += 1

    sample_out = {
        "sample_version": "1.0",
        "drawn": "2026-08-29",
        "purpose": "Held-out calibration set measuring whether kappa=0.650 generalises "
                   "(PROJECT-STATE S2 item 1, JUDGE-RUN-PLAN S6)",
        "seed": SEED,
        "rng": "python random.Random(seed), stdlib Mersenne Twister",
        "source_run": SOURCE_RUN,
        "run_index_fixed": 1,
        "eligibility": "status=='success' and provider!='openrouter' and run_index==1, "
                       "case_id not in calibration/sample.json",
        "excluded_case_ids_source": "04-analysis/calibration/sample.json",
        "n_case_ids_excluded": len(excluded),
        "n_case_ids_available": n_available,
        "stratification": {
            "cells": "one item per (task x model) cell = 5 tasks x 4 scored models = 20",
            "difficulty_totals": difficulty_totals,
            "row_rule": "each task contributes exactly 1 hard; 3 of 5 tasks contribute 1 adversarial",
            "col_rule": "each model contributes exactly 3 typical and 2 non-typical",
            "adversarial_tasks": sorted(ADVERSARIAL_TASKS),
        },
        "blinding": "model_id, provider, model_version and call_id are withheld here; "
                    "the mapping lives in sealed_model_map_heldout.json",
        "items": [
            {
                "item_id": item["item_id"],
                "case_id": item["case_id"],
                "task": item["task"],
                "difficulty": item["difficulty"],
                "run_index": 1,
                "response_sha256": item["response_sha256"],
            }
            for item in drawn
        ],
    }

    map_out = {
        "seed": SEED,
        "source_run": SOURCE_RUN,
        "warning": "SEALED. Do not open until human_scores_heldout.json is complete.",
        "map": [
            {
                "item_id": item["item_id"],
                "case_id": item["case_id"],
                "model_id": item["model_id"],
                "provider": item["provider"],
                "model_version": item["model_version"],
                "call_id": item["call_id"],
                "run_index": 1,
            }
            for item in drawn
        ],
    }

    with open(CAL / "sample_heldout.json", "w", encoding="utf-8") as f:
        json.dump(sample_out, f, indent=2)
    with open(CAL / "sealed_model_map_heldout.json", "w", encoding="utf-8") as f:
        json.dump(map_out, f, indent=2)

    print(f"wrote {len(drawn)} items to sample_heldout.json and sealed_model_map_heldout.json")


if __name__ == "__main__":
    main()

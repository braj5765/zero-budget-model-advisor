"""Flattens 04-analysis/scores.json into 05-site/data/index.json -- only what
the client-side advisor (05-site/advisor/advisor.js) needs, per Decision C1
(static site, client-side advisor over a JSON data file). Drops per-case
detail (case_scores) that belongs to the /results and /model/:id pages, not
the advisor. One responsibility: flatten, don't recompute -- scores.json
remains the source of truth.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCORES_FILE = ROOT / "04-analysis" / "scores.json"
OUT_FILE = ROOT / "05-site" / "data" / "index.json"


def flatten_task(task_data):
    return {
        "task_score": task_data["task_score"],
        "adversarial_sub_score": task_data["adversarial_sub_score"],
        "n_na_dimension_marks": task_data["n_na_dimension_marks"],
        "median_spread": task_data["median_spread"],
        "dimension_means": task_data["dimension_means"],
        "benchmark": task_data["benchmark"],
    }


def main():
    with open(SCORES_FILE, encoding="utf-8") as f:
        scores = json.load(f)

    out = {
        "schema_version": "1.0",
        "rubric_version": scores["rubric_version"],
        "judge_model": scores["judge_model"],
        "judge_provider": scores["judge_provider"],
        "judge_prompt_version": scores["judge_prompt_version"],
        "judged_at": scores["judged_at"],
        "scored_models": scores["scored_models"],
        "models": {},
        "excluded": {},
    }

    for model_id in scores["scored_models"]:
        m = scores["models"][model_id]
        out["models"][model_id] = {
            "tasks": {task: flatten_task(t) for task, t in m["tasks"].items()},
            "rate_limit_ceiling": m["rate_limit_ceiling"],
        }

    or_data = scores["openrouter_excluded_from_quality"]
    out["excluded"]["openrouter-gpt-oss-20b"] = {
        "reason": "Decision A5 -- benchmark run returned 96/300 (32%) success, "
                  "insufficient coverage for median-of-three quality scoring.",
        "benchmark_overall": or_data["benchmark_overall"],
        "rate_limit_ceiling": or_data["rate_limit_ceiling"],
    }

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print(f"Wrote {OUT_FILE}")


if __name__ == "__main__":
    main()

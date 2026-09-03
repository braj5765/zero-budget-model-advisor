"""Aggregates the production judge output into per-model, per-task scores,
strictly per Scoring-Rubric.md S3.6 and S3.7. Reads the two pre-aggregation
audits' conclusions (04-analysis/failure_code_audit.md) as fixed facts rather
than recomputing them here, except where the underlying data (probe.jsonl,
the benchmark run) is cheap and safe to recompute mechanically.

Pipeline, per S3.7 then S3.6:
  median per dimension across the 3 runs (n/a-aware)
  -> case score = mean of applicable dimension medians, normalised to 0-100
  -> task score = mean of the 20 case scores (all 20 count; adversarial 3
     additionally reported as their own sub-score, not double-counted)

Writes 04-analysis/scores.json and prints a readable summary. Deliberately
does not compute an overall ranking or a "best model" figure (Decision A4).
OpenRouter is excluded from quality scoring (Decision A5) but appears in the
failure-rate and rate-limit sections.
"""

import json
import statistics
import tomllib
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CASES_DIR = ROOT / "01-rubric-and-testcases" / "cases"
CONFIG_FILE = ROOT / "02-harness" / "config.toml"
JUDGE_FILE = ROOT / "04-analysis" / "production" / "judge-run-20260828T174641Z.jsonl"
RUN_FILE = ROOT / "03-results" / "run-2026-08-15T114622Z.jsonl"
PROBE_FILE = ROOT / "03-results" / "probe.jsonl"
OUT_FILE = ROOT / "04-analysis" / "scores.json"
SUMMARY_FILE = ROOT / "04-analysis" / "scores-summary.md"

TASK_FILES = {
    "summarization": "summarization.json",
    "extraction": "extraction.json",
    "classification": "classification.json",
    "rag-qa": "rag-qa.json",
    "json-output": "json-output.json",
}

SCORED_MODELS = [
    "gemini-3.5-flash-lite", "groq-llama-3.3-70b",
    "mistral-small-2603", "ollama-llama3.2-3b",
]

# Approximation stated once, used everywhere requests/day is converted to a
# monthly figure. Matches 05-site/advisor/advisor.js's own comment on the
# same constant -- kept in sync by inspection since Python and JS can't
# share a literal; if this changes, that file's copy must change with it.
DAYS_PER_MONTH = 30


def derive_token_ceiling(documented_monthly_tokens, mean_tokens_per_request):
    """The requests/day at which a token-metered provider's monthly ceiling
    binds, for one model x task. This is a COMPUTED figure, not a provider-
    documented one -- it depends on this benchmark's own measured token
    usage, which varies by task and would be wrong to present as a vendor
    number. Returns None where there is no numeric monthly ceiling to derive
    against, or no token data for the task."""
    if not isinstance(documented_monthly_tokens, (int, float)) or mean_tokens_per_request is None:
        return None
    req_per_day = documented_monthly_tokens / mean_tokens_per_request / DAYS_PER_MONTH
    return {
        "req_per_day_at_token_ceiling": round(req_per_day),
        "basis": "derived -- computed from this benchmark's measured mean tokens/request and the "
                 "provider's documented monthly token ceiling. NOT a provider-documented figure; "
                 "varies by task because prompt and response lengths vary by task.",
        "mean_tokens_per_request": round(mean_tokens_per_request, 1),
        "documented_monthly_tokens": documented_monthly_tokens,
        "days_per_month_assumed": DAYS_PER_MONTH,
    }

# Measured ceilings, provenance and notes come from the pre-aggregation audit
# (failure_code_audit.md) -- probe.jsonl's raw rows plus policy facts (Groq's
# "documented + incidental", Ollama's "not applicable") that aren't derivable
# from one file. Documented figures are NOT hand-copied here -- they are read
# from 02-harness/config.toml at runtime (load_documented_ceilings(), below)
# so this table can never drift from the harness's own source of truth again,
# the way judge_prompt.md's dimension names once drifted from judge.py's.
MEASURED_CEILINGS = {
    "gemini-3.5-flash-lite": {
        "measured": {"rpm_at_rejection": 16.6, "requests_before_first_rejection": 39},
        "provenance": "measured",
        "note": "Confirmed by Gemini's own 429 body (limit: 15, generate_content_free_tier_requests).",
    },
    "mistral-small-2603": {
        "measured": {"rpm_at_rejection": 52.1, "requests_before_first_rejection": 96},
        "provenance": "measured",
        "note": "Bare error prose; limit_period_guess left 'unknown', not guessed beyond the string. "
                "The binding ceiling here is token-based (documented_monthly_tokens), not request-based.",
    },
    "groq-llama-3.3-70b": {
        "measured": None,
        "provenance": "documented + incidental",
        "note": "Never actively probed (AUP, ToS-Review R-1). Incidental evidence from the "
                "benchmark run: 8 retries across 7 rows, backoff waits up to 1075s, all "
                "eventually succeeded under the harness's own retry policy.",
    },
    "ollama-llama3.2-3b": {
        "measured": None,
        "provenance": "documented (not applicable)",
        "note": "Local, no network service, no rate limit exists to measure.",
    },
    "openrouter-gpt-oss-20b": {
        "measured": {
            "daily_cap": {"rejections_in_benchmark": 204, "attempts": 300,
                          "limit_source": "openrouter_free_tier_daily"},
            "shared_pool": {"rpm_at_rejection": 24.1, "requests_before_first_rejection": 2,
                             "limit_source": "upstream_provider_shared_pool",
                             "provider_name": "Darkbloom"},
        },
        "provenance": "measured",
        "note": "Two distinct, real ceilings -- an account-level daily cap and a shared-pool "
                "ceiling unrelated to the account's own quota. Both published.",
    },
}


def load_documented_ceilings():
    """Reads documented_rpm/documented_rpd/documented_monthly_tokens/
    documented_source straight from the harness config -- the single source
    of truth for what's documented, so this file can't silently disagree
    with it. TOML preserves the type as written: a numeric limit stays a
    number, "not applicable" or "none documented" stays a string. Nothing
    here coerces a non-numeric ceiling into a number -- callers (and any
    renderer) must handle both types as they come."""
    with open(CONFIG_FILE, "rb") as f:
        config = tomllib.load(f)
    documented = {}
    for m in config["models"]:
        documented[m["id"]] = {
            "documented_rpm": m.get("documented_rpm"),
            "documented_rpd": m.get("documented_rpd"),
            "documented_monthly_tokens": m.get("documented_monthly_tokens"),
            "documented_source": m.get("documented_source"),
        }
    return documented


def load_cases():
    cases = {}
    for task, fname in TASK_FILES.items():
        with open(CASES_DIR / fname, encoding="utf-8") as f:
            data = json.load(f)
        for c in data["cases"]:
            cases[c["case_id"]] = {"task": task, "difficulty": c["difficulty"]}
    return cases


def load_judge_scores():
    """Latest row per (case_id, model_id, run_index) wins, same convention as
    judge_production.py itself."""
    latest = {}
    with open(JUDGE_FILE, encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            key = (r["case_id"], r["model_id"], r["run_index"])
            latest[key] = r
    non_success = [r for r in latest.values() if r["status"] not in ("success", "judged")]
    if non_success:
        raise ValueError(
            f"{len(non_success)} keys have no successful judged row -- aggregation "
            f"requires a complete judged set. First: {non_success[0]}"
        )
    return latest


def median_dimension(vals):
    """S3.7 rule 2: 2+ n/a among the 3 runs -> dimension is n/a for this case.
    Otherwise median of the numeric runs only. Returns (median_or_None, is_na,
    spread_or_None, n_contributing)."""
    n_na = sum(1 for v in vals if v == "n/a")
    if n_na >= 2:
        return None, True, None, 0
    nums = [v for v in vals if v != "n/a"]
    med = statistics.median(nums)
    spread = max(nums) - min(nums)
    return med, False, spread, len(nums)


def case_score(case_id, model_id, judge_by_key, dims):
    """Returns (case_score_0_100, n_na_dims, list_of_(dim, spread) for numeric
    dims, dict_of_dim_to_median_or_None) -- the last so callers can aggregate
    per-dimension means across cases, independent of the case-score mean."""
    medians = []
    n_na = 0
    spreads = []
    dim_medians = {}
    for dim in dims:
        vals = [judge_by_key[(case_id, model_id, r)]["scores"].get(dim, "n/a") for r in (1, 2, 3)]
        med, is_na, spread, _ = median_dimension(vals)
        dim_medians[dim] = None if is_na else med
        if is_na:
            n_na += 1
        else:
            medians.append(med)
            spreads.append((dim, spread))
    if not medians:
        return None, n_na, spreads, dim_medians
    return (sum(medians) / len(medians)) / 3 * 100, n_na, spreads, dim_medians


def aggregate_task(model_id, task, case_ids_by_difficulty, judge_by_key, dims):
    all_case_ids = (case_ids_by_difficulty["typical"] + case_ids_by_difficulty["hard"]
                     + case_ids_by_difficulty["adversarial"])
    case_scores = {}
    n_na_total = 0
    all_spreads = []
    dim_medians_by_case = defaultdict(list)  # dim -> [median, ...] across cases, n/a excluded
    for case_id in all_case_ids:
        score, n_na, spreads, dim_medians = case_score(case_id, model_id, judge_by_key, dims)
        case_scores[case_id] = score
        n_na_total += n_na
        all_spreads.extend(s for _, s in spreads)
        for dim, med in dim_medians.items():
            if med is not None:
                dim_medians_by_case[dim].append(med)

    dimension_means = {
        dim: round((sum(vals) / len(vals)) / 3 * 100, 1) if vals else None
        for dim, vals in dim_medians_by_case.items()
    }

    scored = [s for s in case_scores.values() if s is not None]
    task_score = sum(scored) / len(scored) if scored else None

    adv_ids = case_ids_by_difficulty["adversarial"]
    adv_scored = [case_scores[c] for c in adv_ids if case_scores[c] is not None]
    adv_score = sum(adv_scored) / len(adv_scored) if adv_scored else None

    n_identical = sum(1 for s in all_spreads if s == 0)
    spread_summary = {
        "n_dimension_instances": len(all_spreads),
        "pct_identical_across_runs": round(100 * n_identical / len(all_spreads), 1) if all_spreads else None,
        "mean_spread": round(sum(all_spreads) / len(all_spreads), 3) if all_spreads else None,
        "max_spread": max(all_spreads) if all_spreads else None,
    }

    return {
        "task_score": round(task_score, 1) if task_score is not None else None,
        "adversarial_sub_score": round(adv_score, 1) if adv_score is not None else None,
        "n_cases": len(all_case_ids),
        "n_na_dimension_marks": n_na_total,
        "median_spread": spread_summary,
        "dimension_means": dimension_means,
        "case_scores": {c: (round(s, 1) if s is not None else None) for c, s in case_scores.items()},
    }


def benchmark_stats(model_id, task, run_rows, documented_monthly_tokens=None):
    task_rows = [r for r in run_rows if r["model_id"] == model_id and r["task"] == task]
    n = len(task_rows)
    successes = [r for r in task_rows if r["status"] == "success"]
    failures = [r for r in task_rows if r["status"] != "success"]
    failure_codes = defaultdict(int)
    for r in failures:
        failure_codes[r["failure_code"]] += 1
    latencies = sorted(r["latency_ms"] for r in successes)
    p95_latency = latencies[int(0.95 * (len(latencies) - 1))] if latencies else None
    # Mean tokens/request, this model x task: needed to convert a requests/day
    # volume into a tokens/month figure for providers metered by token
    # volume rather than request count (e.g. Mistral). Computed per model
    # per task, not pooled across models, because tokens_out varies by
    # model even when tokens_in is identical (fixed prompts, Decision B4) --
    # a provider's own token ceiling must be checked against its own
    # token usage, not another model's.
    mean_tokens = (
        sum(r["tokens_in"] + r["tokens_out"] for r in successes) / len(successes)
        if successes else None
    )
    # derive_token_ceiling gets the unrounded mean, not the rounded display
    # value below -- rounding twice would drift the derived figure slightly
    # from what the raw data actually supports.
    derived = derive_token_ceiling(documented_monthly_tokens, mean_tokens)
    return {
        "n_attempts": n,
        "n_success": len(successes),
        "success_rate_pct": round(100 * len(successes) / n, 1) if n else None,
        "failure_code_distribution": dict(failure_codes),
        "p95_latency_ms": p95_latency,
        "mean_tokens_per_request": round(mean_tokens, 1) if mean_tokens is not None else None,
        "derived_token_ceiling": derived,
    }


def main():
    cases = load_cases()
    judge_by_key = load_judge_scores()
    task_dims = defaultdict(set)
    for r in judge_by_key.values():
        task_dims[r["task"]] |= set(r["scores"].keys())

    case_ids_by_task_diff = defaultdict(lambda: defaultdict(list))
    for case_id, info in cases.items():
        case_ids_by_task_diff[info["task"]][info["difficulty"]].append(case_id)

    with open(RUN_FILE, encoding="utf-8") as f:
        run_rows = [json.loads(line) for line in f]

    result = {
        "schema_version": "1.0",
        "rubric_version": "1.7",
        "judge_model": "minimax/minimax-m3:free",
        "judge_provider": "GMICloud",
        "judge_prompt_version": "1.3",
        "judged_at": "2026-08-29",
        "scored_models": SCORED_MODELS,
        "excluded_from_quality_scoring": ["openrouter-gpt-oss-20b"],
        "models": {},
    }

    documented_ceilings = load_documented_ceilings()

    for model_id in SCORED_MODELS:
        model_out = {"tasks": {}}
        monthly_tokens = documented_ceilings[model_id].get("documented_monthly_tokens")
        for task, dims in sorted(task_dims.items()):
            agg = aggregate_task(model_id, task, case_ids_by_task_diff[task], judge_by_key, sorted(dims))
            bench = benchmark_stats(model_id, task, run_rows, monthly_tokens)
            model_out["tasks"][task] = {**agg, "benchmark": bench}
        model_out["rate_limit_ceiling"] = {**documented_ceilings[model_id], **MEASURED_CEILINGS[model_id]}
        result["models"][model_id] = model_out

    # OpenRouter: failure-rate and rate-limit tables only, no quality scoring.
    or_id = "openrouter-gpt-oss-20b"
    or_out = {"tasks": {}}
    for task in sorted(task_dims.keys()):
        or_out["tasks"][task] = {"benchmark": benchmark_stats(or_id, task, run_rows)}
    or_out["benchmark_overall"] = benchmark_stats_overall(or_id, run_rows)
    or_out["rate_limit_ceiling"] = {**documented_ceilings[or_id], **MEASURED_CEILINGS[or_id]}
    result["openrouter_excluded_from_quality"] = or_out

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    print(f"Wrote {OUT_FILE}")
    write_summary(result)
    print(f"Wrote {SUMMARY_FILE}")
    return result


def write_summary(result):
    lines = [
        "# Scores summary — 2026-08-29",
        "",
        f"Rubric v{result['rubric_version']}. Judge `{result['judge_model']}` "
        f"({result['judge_provider']}), prompt v{result['judge_prompt_version']}, "
        f"judged {result['judged_at']}.",
        "",
        "No overall ranking or best-model figure is computed here (Decision A4). "
        "OpenRouter is excluded from quality scoring (Decision A5) and appears only "
        "in the failure-rate and rate-limit sections below.",
        "",
    ]
    for model_id in result["scored_models"]:
        m = result["models"][model_id]
        lines.append(f"## {model_id}")
        lines.append("")
        lines.append("| Task | Score | Adversarial | n/a | Median identical | Success | p95 latency | Failures |")
        lines.append("| :---- | ---: | ---: | ---: | ---: | ---: | ---: | :---- |")
        for task, t in m["tasks"].items():
            sp = t["median_spread"]
            b = t["benchmark"]
            fails = ", ".join(f"{k}:{v}" for k, v in b["failure_code_distribution"].items()) or "—"
            lines.append(
                f"| {task} | {t['task_score']} | {t['adversarial_sub_score']} | "
                f"{t['n_na_dimension_marks']} | {sp['pct_identical_across_runs']}% | "
                f"{b['success_rate_pct']}% | {b['p95_latency_ms']}ms | {fails} |"
            )
        ceil = m["rate_limit_ceiling"]
        lines.append("")
        lines.append(f"Rate-limit ceiling: {format_documented(ceil)}, "
                      f"provenance **{ceil['provenance']}**. {ceil['note']}")
        derived_lines = [
            f"  - {task}: ~{t['benchmark']['derived_token_ceiling']['req_per_day_at_token_ceiling']:,} req/day "
            f"(mean {t['benchmark']['mean_tokens_per_request']} tokens/request measured)"
            for task, t in m["tasks"].items() if t["benchmark"]["derived_token_ceiling"]
        ]
        if derived_lines:
            lines.append("")
            lines.append("**Derived token-ceiling req/day equivalent — computed from measured token "
                          "usage, NOT a provider-documented figure, differs per task:**")
            lines.extend(derived_lines)
        lines.append("")

    lines.append("## openrouter-gpt-oss-20b — excluded from quality scoring, failure-rate/ceiling only")
    lines.append("")
    ov = result["openrouter_excluded_from_quality"]["benchmark_overall"]
    lines.append(f"Overall: {ov['n_success']}/{ov['n_attempts']} succeeded "
                  f"({ov['success_rate_pct']}%), failures: {ov['failure_code_distribution']}.")
    ceil = result["openrouter_excluded_from_quality"]["rate_limit_ceiling"]
    lines.append("")
    lines.append(f"Rate-limit ceiling: {format_documented(ceil)}, "
                  f"provenance **{ceil['provenance']}**. {ceil['note']}")
    lines.append("")

    with open(SUMMARY_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def format_documented(ceil):
    """Never coerces a non-numeric ceiling to a number -- a str value (e.g.
    "not applicable", "none documented") is printed as text, exactly as
    config.toml states it."""
    rpm, rpd = ceil["documented_rpm"], ceil["documented_rpd"]
    if rpm == "not applicable" and rpd == "not applicable":
        return "not applicable"
    parts = [f"documented {rpm} rpm", f"{rpd} rpd"]
    tokens = ceil.get("documented_monthly_tokens")
    if tokens is not None:
        parts.append(f"{tokens:,} tokens/month" if isinstance(tokens, (int, float)) else str(tokens))
    return " / ".join(parts)


def benchmark_stats_overall(model_id, run_rows):
    rows = [r for r in run_rows if r["model_id"] == model_id]
    n = len(rows)
    successes = [r for r in rows if r["status"] == "success"]
    failures = [r for r in rows if r["status"] != "success"]
    failure_codes = defaultdict(int)
    for r in failures:
        failure_codes[r["failure_code"]] += 1
    return {
        "n_attempts": n, "n_success": len(successes),
        "success_rate_pct": round(100 * len(successes) / n, 1) if n else None,
        "failure_code_distribution": dict(failure_codes),
    }


if __name__ == "__main__":
    main()

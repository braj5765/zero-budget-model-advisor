"""Computes judge-vs-human agreement on a calibration set per Scoring-Rubric.md v1.3 S5:
quadratic-weighted Cohen's kappa, Gwet's AC1, both marginals, confusion matrix, raw
agreement, and the count of >=2-point disagreements -- overall, by task, and by dimension.
Then applies the v1.3 four-way decision table. Threshold is fixed at 0.6 and is not a
parameter here.

--human/--judge/--report select which calibration set to score (filenames under
calibration/); defaults reproduce the original in-sample v1.3 hosted run. This
has been re-pointed at a new (human, judge) pair by hand at least four times
already (agreement_report.json, _v1.2, _hosted, _hosted_v1.3) -- CLI args
instead of hand-edited constants, rather than a parallel copy of this file, for
JUDGE-RUN-PLAN S6's held-out run and whatever comes after it.
"""

import argparse
import json
from collections import defaultdict
from pathlib import Path

CAL = Path(__file__).resolve().parents[1] / "calibration"
THRESHOLD = 0.6
CATS = [0, 1, 2, 3]

# judge_prompt.md v1.0's json-output DIMENSIONS block names this dimension
# "constraint_conformance"; human_scores.json (and rubric S3.5) name it
# "enum_constraint_conformance". Same rubric dimension, different label --
# aliased here rather than in the prompt or the human record.
# judge_prompt.md v1.2 renamed rag-qa's "abstention" to "abstention_calibration"
# (disagreement_audit.md #1-#8) -- human_scores.json still uses "abstention",
# aliased the same way.
DIMENSION_ALIASES = {
    "constraint_conformance": "enum_constraint_conformance",
    "abstention_calibration": "abstention",
}


def load_pairs(human_file, judge_file):
    with open(human_file, encoding="utf-8") as f:
        human = json.load(f)
    with open(judge_file, encoding="utf-8") as f:
        judge = json.load(f)

    judge_by_item = {j["item_id"]: j for j in judge["scores"]}
    pairs = []  # (item_id, task, dimension, human_score, judge_score)
    violations = []  # unsanctioned n/a -- judge.py's na_eligible_dimensions() rejected these
    for h in human["scores"]:
        j = judge_by_item[h["item_id"]]
        j_violations = set(j.get("na_protocol_violations", []))
        for dim, hval in h["dimensions"].items():
            jkey = dim if dim in j["scores"] else next(
                (k for k, v in DIMENSION_ALIASES.items() if v == dim), dim
            )
            jval = j["scores"].get(jkey, j["scores"].get(dim))
            if jkey in j_violations:
                violations.append((h["item_id"], h["task"], dim, hval, jval))
                continue
            if jval == "n/a" or hval == "n/a":
                # sanctioned n/a (case-design-eligible) on either side -- excluded
                # from the denominator per rubric S3.6 rule 2, not a violation.
                continue
            pairs.append((h["item_id"], h["task"], dim, int(hval), int(jval)))
    return pairs, violations


def confusion(pairs):
    O = [[0] * 4 for _ in CATS]
    for _, _, _, h, j in pairs:
        O[h][j] += 1
    return O


def marginals(O):
    row = [sum(O[i][j] for j in CATS) for i in CATS]
    col = [sum(O[i][j] for i in CATS) for j in CATS]
    return row, col


def quadratic_weighted_kappa(O):
    n = sum(sum(r) for r in O)
    if n == 0:
        return None
    row, col = marginals(O)
    E = [[row[i] * col[j] / n for j in CATS] for i in CATS]
    W = [[((i - j) ** 2) / 9.0 for j in CATS] for i in CATS]
    num = sum(W[i][j] * O[i][j] for i in CATS for j in CATS)
    den = sum(W[i][j] * E[i][j] for i in CATS for j in CATS)
    if den == 0:
        return 1.0 if num == 0 else None
    return 1 - num / den


def gwet_ac1(O):
    n = sum(sum(r) for r in O)
    if n == 0:
        return None
    row, col = marginals(O)
    po = sum(O[i][i] for i in CATS) / n
    pi = [(row[k] / n + col[k] / n) / 2 for k in CATS]
    q = len(CATS)
    pe = sum(p * (1 - p) for p in pi) / (q - 1)
    if pe == 1:
        return 1.0 if po == 1 else 0.0
    return (po - pe) / (1 - pe)


def raw_agreement(pairs):
    n = len(pairs)
    agree = sum(1 for *_, h, j in pairs if h == j)
    return agree / n if n else None


def big_disagreements(pairs):
    return [p for p in pairs if abs(p[3] - p[4]) >= 2]


def stats_block(pairs):
    O = confusion(pairs)
    row, col = marginals(O)
    return {
        "n": len(pairs),
        "confusion_matrix": O,
        "human_marginal": row,
        "judge_marginal": col,
        "raw_agreement": raw_agreement(pairs),
        "quadratic_weighted_kappa": quadratic_weighted_kappa(O),
        "gwet_ac1": gwet_ac1(O),
        "n_ge2_disagreements": len(big_disagreements(pairs)),
    }


def decide(overall, by_task, by_dim):
    kappa = overall["quadratic_weighted_kappa"]
    ac1 = overall["gwet_ac1"]
    n_big = overall["n_ge2_disagreements"]

    task_concentration = any(
        b["n_ge2_disagreements"] > 0 and b["n_ge2_disagreements"] == n_big and n_big > 0
        for b in by_task.values()
    )
    dim_concentration = any(
        b["n_ge2_disagreements"] > 0 and b["n_ge2_disagreements"] == n_big and n_big > 0
        for b in by_dim.values()
    )
    concentrated = (task_concentration or dim_concentration) and n_big > 0

    if kappa is not None and kappa >= THRESHOLD:
        action = "PROCEED to the full set (kappa >= 0.6)."
    elif kappa is not None and ac1 is not None and ac1 >= THRESHOLD and n_big == 0 and not concentrated:
        action = ("PREVALENCE ARTIFACT, not judge failure. Extend the calibration set with "
                  "10 additional hard/adversarial items and recompute. Threshold NOT lowered.")
    elif kappa is not None and ac1 is not None and ac1 < THRESHOLD:
        action = "REAL DISAGREEMENT. Sharpen rubric anchors, re-judge the 20, retry per S5."
    else:
        action = ("kappa < 0.6 with >=1 disagreement of >=2 points present (or concentration "
                  "detected): does not qualify as a clean prevalence artifact. Treat as REAL "
                  "DISAGREEMENT -- sharpen anchors, re-judge, retry per S5.")

    if n_big > 0:
        action += (f" ALSO: {n_big} disagreement(s) of >=2 points exist -- per the 'any "
                  ">=2-point disagreement' row, these must be audited and written up "
                  "before proceeding, regardless of kappa.")
    return action


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--human", default="human_scores.json", help="Filename under calibration/.")
    ap.add_argument("--judge", default="judge_scores_hosted_v1.3.json",
                    help="Filename under calibration/.")
    ap.add_argument("--report", default="agreement_report_hosted_v1.3.json",
                    help="Filename under calibration/ to write.")
    args = ap.parse_args()

    pairs, violations = load_pairs(CAL / args.human, CAL / args.judge)
    overall = stats_block(pairs)

    by_task = defaultdict(list)
    for p in pairs:
        by_task[p[1]].append(p)
    by_task_stats = {t: stats_block(v) for t, v in by_task.items()}

    by_dim = defaultdict(list)
    for p in pairs:
        by_dim[p[2]].append(p)
    by_dim_stats = {d: stats_block(v) for d, v in by_dim.items()}

    report = {
        "threshold": THRESHOLD,
        "overall": overall,
        "by_task": by_task_stats,
        "by_dimension": by_dim_stats,
        "big_disagreements": [
            {"item_id": i, "task": t, "dimension": d, "human": h, "judge": j}
            for i, t, d, h, j in big_disagreements(pairs)
        ],
        "na_protocol_violations": [
            {"item_id": i, "task": t, "dimension": d, "human": h, "judge": j}
            for i, t, d, h, j in violations
        ],
        "n_na_protocol_violations": len(violations),
        "decision": decide(overall, by_task_stats, by_dim_stats),
    }

    with open(CAL / args.report, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

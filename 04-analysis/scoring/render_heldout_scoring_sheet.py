"""Renders calibration/scoring_sheet_heldout.json: everything needed to
hand-score the held-out set from Scoring-Rubric.md alone, with model
identity stripped and item order as drawn (already randomised by
draw_heldout_sample.py). Reuses judge_common's case loading and gold
formatting -- the same content the judge itself sees, minus the judge-only
scale/anchors text, since the human scorer works from the rubric directly
(human_scores.json's own protocol line), not from the judge's crib sheet.

Resolves each item's response_text by (case_id, response_sha256) in the run
file, the same match judge.py uses -- never via sealed_model_map_heldout.json,
so this script never has to open the sealed file.
"""

import hashlib
import json
from pathlib import Path

from judge_common import ROOT, format_gold, load_cases, load_run_rows

CAL = ROOT / "04-analysis" / "calibration"
OUT_FILE = CAL / "scoring_sheet_heldout.json"

# Dimension keys as human_scores.json (and Scoring-Rubric.md) name them --
# judge_common.DIMENSIONS uses judge-prompt aliases for two of these
# (constraint_conformance, abstention_calibration; see agreement.py).
HUMAN_DIMENSIONS = {
    "summarization": ["faithfulness", "coverage", "concision", "instruction_adherence"],
    "extraction": ["precision", "recall", "normalisation", "null_handling"],
    "classification": ["label_correctness", "label_validity", "ambiguity_handling"],
    "rag-qa": ["groundedness", "answer_correctness", "abstention", "citation_accuracy"],
    "json-output": ["parseability", "schema_conformance", "enum_constraint_conformance",
                     "content_correctness"],
}


def find_response(rows, case_id, response_sha256):
    for r in rows:
        if (r["case_id"] == case_id and r["run_index"] == 1 and r["status"] == "success"
                and hashlib.sha256(r["response_text"].encode("utf-8")).hexdigest() == response_sha256):
            return r["response_text"]
    raise ValueError(f"no matching response for {case_id}")


def main():
    with open(CAL / "sample_heldout.json", encoding="utf-8") as f:
        sample = json.load(f)
    cases = load_cases()
    rows = load_run_rows()

    sheet = []
    for item in sample["items"]:
        case = cases[item["case_id"]]
        response_text = find_response(rows, item["case_id"], item["response_sha256"])
        sheet.append({
            "item_id": item["item_id"],
            "case_id": item["case_id"],
            "task": item["task"],
            "difficulty": item["difficulty"],
            "instruction": case["instruction"],
            "source": case.get("source") or {
                "passages": case.get("passages"), "question": case.get("question"),
            },
            "gold": format_gold(item["task"], case["gold"]),
            "probes": case["probes"],
            "gold_notes": case["gold"].get("notes", ""),
            "response_text": response_text,
            "dimensions": {dim: None for dim in HUMAN_DIMENSIONS[item["task"]]},
            "na_reasons": {},
            "note": "",
            "scored_at": "",
        })

    out = {
        "schema_version": "1.0",
        "rubric_version": "1.7",
        "scorer": "Braj (human, blind)",
        "protocol": "Blind hand-scoring from Scoring-Rubric.md v1.7 only. Model identity "
                    "withheld until scoring complete (sealed_model_map_heldout.json). "
                    "Scale 0-3 per rubric S2. 'n/a' per S3.6 rule 1 only where case design "
                    "makes a dimension unscoreable.",
        "sample": "04-analysis/calibration/sample_heldout.json",
        "seed": sample["seed"],
        "items": sheet,
    }
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print(f"wrote {len(sheet)} items to {OUT_FILE.name}")


if __name__ == "__main__":
    main()

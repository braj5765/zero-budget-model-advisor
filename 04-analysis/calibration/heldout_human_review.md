# Held-out human-error review — Braj's adjudication, 2026-08-31

**This review was conducted by the human scorer (Braj) *after* seeing the judge's scores. It is not blind, and that limitation is inherent to the exercise, not an oversight — a genuinely blind re-check would require a third, unscored calibration set, which does not exist. It is recorded here rather than left implicit.**

**Purpose and what this does not do.** `disagreement_audit_heldout.md` classified 5 of the held-out set's 7 ≥2-point disagreements as "judge correct, human score diverges from a documented rule." Because that classification was made by an LLM (this session's assistant) about a disagreement between itself's own judge model and a human, it carries an unavoidable self-preference risk that none of Decision B3's controls (judge outside the benchmarked model set, blinding, order randomisation) address — B3 controls for the *judge's* bias against the *benchmarked models*, not for a reviewing LLM's bias in favour of an LLM judge it is evaluating. This document is Braj's independent check of that classification, presented one item at a time with the case's own documented rule quoted verbatim and sourced, with no argument or steering from the assistant. It does **not** change any score in `human_scores_heldout.json`, does **not** recompute κ (0.358 stands as published, per JUDGE-RUN-PLAN §6), and does **not** touch the rubric or `judge_prompt.md`. It informs what remedy is appropriate, not what the number is.

---

## 1. cal-h01 · jsn-t04 · `parseability` — human 3, judge 0

**Rule:** `json-output.json` file-level `conventions.raw_capture`: *"Fence-wrapping and wrapper prose are parseability failures and are scored as such (rubric §3.5)."*

**Braj's verdict: I missed the rule.**

**Reasoning given:** "the back ticks shouldn't be there ideally and there presence makes the score 0"

---

## 2. cal-h05 · ext-a02 · `precision` — human 3, judge 0

**Rule:** `Scoring-Rubric.md` §3.2 Precision anchor (*"...or lower where that content is not in the source at all, which is fabrication"*) plus case `ext-a02`'s own `gold.notes` naming the committed date and currency values as the adversarial target, scored 0.

**Braj's verdict: I missed the rule.**

**Reasoning given:** "I missed the rule here, both in case of the date and currency part"

---

## 3. cal-h05 · ext-a02 · `normalisation` — human 2, judge 0

**Rule:** case `ext-a02`'s `gold.notes`: *"committing to either without signalling the ambiguity scores 0 on normalisation, however confidently phrased... 15/08/2026 is NOT ambiguous — no month is 15 — so it must be resolved to 2026-08-15, and returning null for it is over-abstention and scores 1... returning 'USD' is the most common failure and scores 0 on normalisation."*

**Braj's verdict: I missed the rule.**

**Reasoning given:** "I missed the rule in this case also, overlooking date format ambiguity like previous one here and also the the writing of 15 as month thing"

---

## 4. cal-h05 · ext-a02 · `null_handling` — human 3, judge 0

**Rule:** `Scoring-Rubric.md` §3.2 Null handling anchor: *"Fabrication scores 0; nulling a determinable value scores 1."* Gold requires both ambiguous fields null with `_raw` companions; the response committed values to both instead.

**Braj's verdict: I missed the rule.**

**Reasoning given:** "I missed the rule here again, similar miss of date format ambiguity and also currency thing"

---

## 5. cal-h12 · sum-a02 · `coverage` — human 3, judge 1

**Rule:** case `sum-a02`'s `gold.notes`: *"Coverage scores 0 if the search defect is omitted, and 1 if it is mentioned only as one item in a list of equals. Scoring 3 requires the summary to foreground it."*

**Braj's verdict: I missed the rule.**

**Reasoning given:** "I missed the part of intelligent summarization here and scored it 3 so mere condensing"

---

## Count

**5 of 5: human scoring error, confirmed by the human scorer.** The judge's classification of these 5 disagreements as "judge correct, human diverges" in `disagreement_audit_heldout.md` is upheld on independent, non-blind adjudication by the original scorer, against the case's own documented rules in each instance.

This does not touch the remaining 2 of the audit's 7 disagreements (`cal-h11`'s `recall`, classified as genuine prompt/anchor ambiguity, and `cal-h11`'s `null_handling`, classified as judge incapacity) — neither was presented here, and neither verdict is confirmed or revised by this review.

**What this does and does not imply for κ=0.358.** The published held-out κ is unchanged and stands as the measurement. But it means that of the 76 human-scored dimension-pairs in this held-out pass, at least 5 carry a scoring error the human scorer has now confirmed against documented rules they had access to at scoring time. That is a data point about this particular hand-scoring pass's reliability on adversarial/edge-case items with explicit `gold.notes`, not about the judge's ability to generalise — and it bears directly on JUDGE-RUN-PLAN §6's fallback: a hand-scored reduced set is not automatically more reliable than the judge on these dimensions unless scored with the case notes checked line by line, which is exactly what this adjudication pass did and the original blind pass did not.

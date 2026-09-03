# Disagreement Audit — Held-out 20-item set, MiniMax-M3 (hosted) vs human, judge_prompt.md v1.3 (frozen)

**Required by Scoring-Rubric.md §5 rule 4 — fires regardless of κ, and this round does not clear it.** Source: `04-analysis/calibration/agreement_report_heldout.json.big_disagreements` (7 pairs across 4 items, n=73 pooled). Judge: `minimax/minimax-m3:free` via GMICloud — identical configuration to the in-sample v1.3 run. Prompt: `judge_prompt.md` v1.3, **frozen, unmodified**, per JUDGE-RUN-PLAN §6's pre-commitment. Human scorer: Braj, blind, Scoring-Rubric.md v1.7. No case_id here overlaps `calibration/sample.json`'s 20.

**Result: κ = 0.358, AC1 = 0.689, raw agreement 72.6%, ≥2-point disagreements 7 (of n=73 pooled pairs).** This falls in JUDGE-RUN-PLAN §6's `< 0.45` band. Compare the in-sample v1.3 run: κ = 0.650, AC1 = 0.779, raw agreement 80.3%, 4 disagreements.

**Headline finding, stated before the item-by-item detail because it changes how the number should be read: 5 of these 7 disagreements are not judge failures at all.** In each of those five the judge's score matches a documented, unambiguous scoring rule — either the json-output file's own project-wide fencing convention or the specific case's own `gold.notes` — verbatim, and the human's score is the one that diverges from it. Only one disagreement is a genuine, novel anchor-boundary ambiguity, and one is a real judge misapplication of its own anchor's explicit numeric mapping. This is close to the inverse of the in-sample v1.3 audit's finding (4 of 4 prompt ambiguity, 0 judge incapacity, 0 human error). It does not change which §6 band the result falls into — that reading is fixed to the κ number itself, deliberately, so it can't be reshaped by attribution — but it is directly relevant to interpreting what a low held-out κ means here, and to how much weight a hand-scored fallback should be given if triggered.

---

## 1. cal-h01 · jsn-t04 · `parseability` — human 3, judge 0

Response: ` ```json\n{...}\n``` ` — fenced.

This case's own `probes`/`gold.notes` are about the `tools` array-vs-string schema point, not about fences at all — but `json-output.json`'s file-level `conventions.raw_capture` states, for every case in the file: *"Fence-wrapping and wrapper prose are parseability failures and are scored as such (rubric §3.5)."* `conventions.parseability_gate` then states the object is left unscored on the other three dimensions, not scored 0, once parseability fails. Both are exactly what the judge did: parseability 0, the other three `n/a`.

**Verdict: JUDGE CORRECT — matches a project-wide, unambiguous rule.** Not prompt ambiguity (the rule is explicit and file-level, not case-specific) and not judge incapacity (the judge applied it correctly). The human score diverges from a documented rule, most plausibly because this case's own notes point attention at the array-vs-string probe and say nothing about fencing — a plausible mechanism, not an excuse; the rule applies regardless of what a given case is designed to probe.

**Side effect worth flagging on its own: this one disagreement removes 3 more dimension-pairs from the panel, not just 1.** `agreement.py` excludes a pair from `n` whenever *either* rater says `n/a` (rubric §3.6 rule 2) — correct when both raters agree the dimension is unscoreable, but here the human confidently scored all three content dimensions 3, i.e. the human's position is that they *are* scoreable. The exclusion is driven entirely by the judge's own (correct) parseability call cascading into `na_eligible_dimensions()`. The result: `n` drops from 76 to 73, and only 1 of the 4 real human/judge divergences on this item shows up as a counted disagreement — the other 3 vanish into "no data" rather than "disagreement." Not a bug against the rule as written, but worth naming: the exclusion rule assumes symmetric agreement that a dimension is moot, and silently absorbs disagreement when that assumption doesn't hold.

---

## 2–4. cal-h05 · ext-a02 · `precision` (3→0), `normalisation` (2→0), `null_handling` (3→0)

This is extraction's adversarial ambiguous-date/ambiguous-currency case (the same one named in PROJECT-STATE §8's 2026-08-11 extraction entry). `gold.notes` states, verbatim: *"committing to either without signalling the ambiguity scores 0 on normalisation, however confidently phrased"* (for the date) and *"returning 'USD' is the most common failure and scores 0 on normalisation"* (for the currency) — and gold's `expected` requires `first_payment_date: null` / `first_payment_currency: null` with `_raw` companions carrying the original ambiguous text.

The response committed to `"first_payment_date": "2026-07-04"` and `"first_payment_currency": "USD"` on both ambiguous fields — no `_raw`, no null, no hedge. This is precisely the failure mode the case's own notes name as the adversarial target and score 0. Judge's precision=0 and null_handling=0 both track the null_handling anchor's plain mapping (fabrication → 0) applied to a case whose own notes confirm these committed values count as fabrication, not a defensible reading.

**Verdict, all three: JUDGE CORRECT — matches the case's own authoritative `gold.notes` verbatim.** Not ambiguous: the notes spell out the exact 0-mapping for exactly this failure mode. The human's generous scores read the response as a plausible, confident answer without checking it against the case's explicit ambiguity design — the same pattern as items 1 and 7 below, on the case in the whole held-out set most deliberately built to punish exactly that read.

---

## 5. cal-h11 · ext-h05 · `recall` — human 3, judge 1

Source: a delivery note naming the recipient informally ("Santerre Épicerie — order received") rather than under a labelled field, unlike `driver_name` which is explicitly labelled ("Driver: M. Cissé"). Gold requires `recipient: "Santerre Épicerie"` — determinable, no ambiguity flagged in this case's `probes` or `notes` (those discuss `signed_by` as the deliberate trap, not `recipient`). The response nulled `recipient`.

Judge's recall justification cites two things: the nulled recipient, **and** "item descriptions conflate quantity with description instead of cleanly extracting them" — but quantity *was* extracted as its own field (`"quantity": 4`) alongside a description that redundantly repeats it; that's a normalisation/formatting complaint, not a recall matter, since nothing is missing. The recall anchor and the extraction dimension table don't say whether an incorrectly-*nulled* present field should be charged against recall, against null_handling, or (as the judge did) partly against recall via a formatting complaint that belongs to normalisation instead.

**Verdict: PROMPT/ANCHOR AMBIGUITY — a new instance, not the known one.** This project's precision/normalisation boundary gap (flagged in the in-sample v1.2-hosted and v1.3-hosted audits, still open) is about a different pair of dimensions. This is a recall/normalisation boundary with no stated owner, surfaced by the held-out draw's `ext-h05`, which the in-sample set's `ext-a03`/`ext-h03` didn't happen to exercise this way. Neither score is clearly right: human's 3 gives the recipient miss no weight at all; judge's 1 double-counts a formatting issue that isn't a recall issue.

---

## 6. cal-h11 · ext-h05 · `null_handling` — human 3, judge 0

Same item. Judge's own justification: *"The model fabricated no values, but it nulled the determinable recipient... which is over-abstention on a clearly resolvable field."* The null_handling anchor states plainly: *"Fabrication scores 0; nulling a determinable value scores 1."* The judge's own text describes the over-nulling case, not the fabrication case — by the anchor's explicit, unambiguous mapping this should score 1. It scored 0.

**Verdict: JUDGE INCAPACITY.** Not an ambiguous anchor — the anchor states the 0-vs-1 split in one sentence — and not a case-notes conflict (this case's notes don't touch `recipient`). The judge's own justification contradicts its own number.

---

## 7. cal-h12 · sum-a02 · `coverage` — human 3, judge 1

Summarization's buried-lede adversarial case. `gold.notes`: *"Coverage scores 0 if the search defect is omitted, and 1 if it is mentioned only as one item in a list of equals. Scoring 3 requires the summary to foreground it."* The response's fourth and final sentence mentions the defect with correct detail, but as one item in a flat list alongside routine items (search reindex, onboarding, a flaky test fix) — no signal that it is the significant fact, matching the notes' own description of the "1" case exactly, not the "3" case.

**Verdict: JUDGE CORRECT — matches the case's own explicit, unambiguous scoring rule.** The notes give a literal three-way rubric (0/1/3) for exactly this scenario; the judge applied the middle branch correctly. The human's 3 appears to credit the fact's presence without checking the case's foregrounding requirement — the same failure mode as items 1–4.

---

## Summary

| # | Item | Dimension | Human | Judge | Verdict |
|---|------|-----------|:---:|:---:|---|
| 1 | cal-h01 | parseability | 3 | 0 | Judge correct — matches project-wide fencing convention; human score diverges |
| 2 | cal-h05 | precision | 3 | 0 | Judge correct — matches case's own adversarial gold notes |
| 3 | cal-h05 | normalisation | 2 | 0 | Judge correct — matches case's own adversarial gold notes |
| 4 | cal-h05 | null_handling | 3 | 0 | Judge correct — matches case's own adversarial gold notes |
| 5 | cal-h11 | recall | 3 | 1 | Prompt/anchor ambiguity — new recall/normalisation boundary gap |
| 6 | cal-h11 | null_handling | 3 | 0 | Judge incapacity — misapplied its own anchor's explicit 0-vs-1 mapping |
| 7 | cal-h12 | coverage | 3 | 1 | Judge correct — matches case's own explicit buried-lede rule |

**5 of 7 judge-correct/human-diverges, 1 prompt/anchor ambiguity (novel), 1 judge incapacity, 0 cases where the human's more generous read is the defensible one.** Contrast with the in-sample v1.3 audit's 4 of 4 prompt ambiguity, 0 judge incapacity, 0 human divergence — the composition is nearly inverted.

**What this does and doesn't mean for the κ=0.358 result.** It doesn't move which JUDGE-RUN-PLAN §6 band the result falls into — that reading is fixed to the number itself, deliberately, precisely so it can't be reshaped by after-the-fact attribution. But it means a large share of what depresses held-out κ is this specific human-scoring pass diverging from documented, checkable rules on adversarial and edge-case items — not the judge failing to generalize to unseen cases. If the §6 fallback is invoked, that is worth weighing: hand-scoring is not obviously more reliable than the judge on these particular dimensions in this particular pass, and a reduced hand-scored set inherits the same risk unless scored with the case notes checked line by line rather than read holistically.

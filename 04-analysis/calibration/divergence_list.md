# Divergence List — Scoring-Checklist.md vs. all four score files

**Complete sweep.** Every dimension pair, every item, both calibration sets (`human_scores.json` × `judge_scores_hosted_v1.3.json`, 76 pairs; `human_scores_heldout.json` × `judge_scores_heldout.json`, 76 raw / 73 after `n/a` exclusion) — not just the ≥2-point subset the original disagreement audits covered. A rule was applied wherever human and judge disagreed by any margin, including 1 point; matching pairs were re-examined wherever another dimension on the same item was already flagged, to catch a same-cause bleed into an agreeing dimension. No shortcuts to ≥2-point gaps.

**Standard.** A divergence is reported only where a checklist rule's text, combined with the recorded justification (or, for structural rules, the recorded score pattern itself), *determines* a score — not wherever human and judge merely disagree. Where §8.1 (precision/normalisation) or §8.2 (recall/normalisation/null-handling) makes the checklist explicitly agnostic, or a dimension's rubric anchor gives only 3/0 poles with no way to place a mid-scale score other than "by degree," no divergence is asserted even if a disagreement exists.

**Gaps set aside on the open-boundary basis: 6.** cal-06 `normalisation` (ext-a03), cal-11 `normalisation` (ext-t04, precision/normalisation blend on the `location` field), cal-16 `precision` (ext-h03, double-charge with normalisation not cleanly separable), cal-h11 `normalisation` (ext-h05, same double-charge pattern), cal-h14 `normalisation` (ext-t07) — all §8.1. cal-h11 `recall` (ext-h05) — §8.2. Two of these (cal-h14, cal-06 amounts) also surface a related, narrower gap: the canonical-form definitions in `extraction.json` `conventions` (§9.4) are silent on whether trailing decimal notation (`3150.0` vs `3150`) counts as non-canonical — genuinely undecidable from the stated rules, not resolved here. Separately, a large population of ordinary 1-vs-2 "by degree" gaps (concision/instruction_adherence length judgments, coverage partial-credit without a named probed point) were reviewed and found non-determinate by design — the rubric anchors only the 3 and 0 poles on most dimensions — these are not counted in the six above since they are not §8.1/§8.2 boundary cases, just the expected imprecision of a 4-point scale anchored at two ends.

---

## (a) The 10 already adjudicated — `heldout_human_review.md` / `disagreement_audit_heldout.md`

| # | Item | Set | Dimension | Rule (source) | Checklist implies | Human recorded | Judge recorded | Diverges from |
|---|---|---|---|---|---|---|---|---|
| 1 | cal-h01 (jsn-t04) | held-out | parseability | Checklist §5.1 rule 2 (rubric §3.5 table: "no wrapper prose or fences") | 0 | 3 | 0 | human |
| 2 | cal-h01 | held-out | schema_conformance | Checklist §5.1 rule 3 (rubric §3.5 italic note, n/a on parseability=0) | n/a | 3 | n/a | human |
| 3 | cal-h01 | held-out | enum_constraint_conformance | Checklist §5.1 rule 3 | n/a | 3 | n/a | human |
| 4 | cal-h01 | held-out | content_correctness | Checklist §5.1 rule 3 | n/a | 3 | n/a | human |
| 5 | cal-h05 (ext-a02) | held-out | precision | Checklist §2.1 rule 3 (rubric §3.2 precision anchor: fabrication) + case `gold.notes` | 0 | 3 | 0 | human |
| 6 | cal-h05 | held-out | normalisation | Checklist §2.3 rule 1 + case `gold.notes` (committing to ambiguous date/currency without signalling scores 0) | 0 | 2 | 0 | human |
| 7 | cal-h05 | held-out | null_handling | Checklist §2.4 rule 1 (rubric §3.2 null-handling anchor: fabrication) | 0 | 3 | 0 | human |
| 8 | cal-h11 (ext-h05) | held-out | null_handling | Checklist §2.4 rule 2 (rubric §3.2 anchor: nulling a determinable value scores 1 — not 0, not 3) | 1 | 3 | 0 | **both** |
| 9 | cal-h12 (sum-a02) | held-out | coverage | Checklist §1.2 rules 2–3 + case `gold.notes` (0/1/3 buried-lede rubric) | 1 | 3 | 1 | human |

*(9 unique dimension-cases; cal-h11's null_handling counts once here and is the one instance touching both files, which is why the earlier round reported "10 instances.")*

---

## (b) The 3 found completing the §9-rule check (prior round)

| # | Item | Set | Dimension | Rule (source) | Checklist implies | Human recorded | Judge recorded | Diverges from |
|---|---|---|---|---|---|---|---|---|
| 10 | cal-18 (cls-t07) | in-sample | ambiguity_handling | Checklist §9.1, "unwarranted hedging costs a point" (`judge_prompt.md` v1.2 classification ANCHOR — **not in rubric**) | 2 | 3 | 2 | human |
| 11 | cal-h17 (cls-h03) | held-out | ambiguity_handling | Checklist §3.3 rule 2 (**base rubric** §3.3 table, 0-cell: "picks confidently and wrongly with no signal of uncertainty" — judge's own justification confirms no `Note:` line was used) | 0 | 1 | 0 | human |
| 12 | cal-h15 (rag-t10) | held-out | abstention_calibration | Checklist §9.2, two-branch rule (`judge_prompt.md` v1.2 — **not in rubric**): answering an ANSWERABLE question is never a deduction here regardless of `answer_correctness` | 3 | 2 | 3 | human |

---

## (c) New — found completing the full sweep this round

| # | Item | Set | Dimension | Rule (source) | Checklist implies | Human recorded | Judge recorded | Diverges from |
|---|---|---|---|---|---|---|---|---|
| 13 | cal-09 (sum-t10) | in-sample | faithfulness | Checklist §1.1 (**base rubric** §3.1 table: faithfulness = claim traceability/invention only). Judge's own justification: *"All stated figures match the source, but the response omits..."* — omission is not a faithfulness criterion under the rubric's own definition; it is coverage's | 3 | 3 | 2 | **judge** |
| 14 | cal-17 (sum-h03) | in-sample | coverage | Checklist §1.2 rule 3b (**base rubric** §3.1 coverage anchor, v1.4). Judge's own words match the rule's own wording verbatim: *"which the four-sentence length could have accommodated"* | 2 | 3 | 2 | human |
| 15 | cal-17 (sum-h03) | in-sample | instruction_adherence | Checklist §1.4 rules 1 & 4 (**base rubric** §3.1 table + anchor's double-counting clause). Judge confirms format/length/exclusion of unrelated remarks were all honoured, then deducts solely for *"it omits the resolution detail"* — the identical omission already charged (correctly) to coverage on this same item (#14) | 3 | 3 | 2 | **judge** |

Item 15 and item 14 are the same underlying defect (an omitted "resolution" detail) charged to two different dimensions on the same response — coverage correctly, instruction_adherence incorrectly. This is the clearest instance in the sweep of a rule the anchor itself warns against (§3.1's coverage anchor: "double-counts the same behaviour").

---

## The three counts

1. **Divergences against a human score, where the judge matches the checklist: 12.** (#1–7, #9–12, #14)
2. **Divergences against a judge score, where the human matches the checklist: 2.** (#13, #15)
3. **Divergences against both: 1.** (#8)

**12 + 2 + 1 = 15 total** (16 counting cal-h11's null_handling once per file, as the earlier round's "10" did).

**Category 2 is not zero.** Both of its members (#13, #15) are sourced from base rubric §3.1 — the faithfulness table cell and the coverage anchor's own double-counting clause — not from §9's judge_prompt-consolidated rules. That is the answer to the tautology concern raised last round: §9 rules share a source with the judge (`judge_prompt.md`), so a judge-favouring result there would be close to tautological. These two do not share that source — they come from the same rubric the human scored from — and the judge still violated them. Category 1's #11 (cal-h17) is the same: sourced from the base rubric table, not §9, and still a human miss. The checklist catches errors on both sides of the judge/human split, from rules neither side has an inherent sourcing advantage on.

---

*No score changed. No rubric, judge prompt, or case file touched. No adjudication performed — this file lists what the checklist implies against what was recorded; it does not rule on which is correct. Set 3 not drawn.*

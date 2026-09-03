# Disagreement Audit — 20-item calibration, MiniMax-M3 (hosted) vs human, judge_prompt.md v1.3

**Required by Scoring-Rubric.md v1.3 §5 rule 4 — fires regardless of κ, and κ cleared this round.** Source: `04-analysis/calibration/agreement_report_hosted_v1.3.json.big_disagreements` (4 pairs, n=76 pooled). Judge: `minimax/minimax-m3:free` via GMICloud, unchanged from the v1.2 hosted run. Only change from that run: `judge_prompt.md` v1.3 adds `{{PROBES}}`, populated from each case's `probes` field, ahead of `{{GOLD_NOTES}}`.

**Result: κ = 0.650 (clears 0.6), AC1 = 0.779, raw agreement 80.3%, ≥2-point disagreements 6 → 4.** Two of the four v1.2-hosted disagreements resolved to 1-point gaps (cal-09's `faithfulness`, cal-14's `concision`); the other two persist unchanged (cal-14's `faithfulness`, `coverage`, `instruction_adherence` — still 3 of 4 dims on this one item); and one new ≥2-point gap appeared (cal-06's `normalisation`) that wasn't flagged before.

---

## 1–3. cal-14 · sum-a01 · `faithfulness` (3→1), `coverage` (1→3), `instruction_adherence` (3→1)

**The falsification test from the v1.3 changelog entry:** adding `probes` cannot move any human score, since the human already had it. It didn't — `human_scores.json` is untouched. What moved is what the judge does with the field now that it's supplied.

**It reached the judge.** `instruction_adherence`'s justification now reads: *"includes the speculative causal language the case was designed to probe against"* — language that only makes sense if the judge saw the case's `probes` field (*"HALLUCINATION BY INFERENCE — source invites a causal conclusion it does not state"*), which v1.2 never supplied. This is a real, checkable behavior change, not a restatement.

**But `coverage` didn't move.** Justification: *"Captures all key points: the 34% rise with numbers, the billing surge, the categorisation breakdown with proration noted, the 940 uncategorised, the pricing launch, renewals, campaign, and agents on leave."* Still the point-counting the coverage anchor forbids, still missing the cap-at-1 rule for the probed point — on the same item where the judge's *own other dimensions* now demonstrably reference that exact probe. **Diagnosis: the input gap is closed, but a reasoning gap remains** — the judge holds "this case probes causal-inference hallucination" as a fact (visibly, in its `faithfulness` and `instruction_adherence` reasoning) without connecting it to the specific instruction, stated only in the coverage anchor earlier in the prompt, that missing the probed point caps *coverage* at 1. Supplying the fact didn't supply the cross-reference between where the rule lives and where the fact now lives.

**`faithfulness` (1, was 0) and `instruction_adherence` (1, unchanged) still disagree with human's 3 for the same reason flagged in the v1.2-hosted audit:** the judge reads *"may have contributed to the higher ticket volume"* (about agent leave) as the forbidden causal claim, when gold's `must_not_include` names only pricing-page causation. `probes` naming the trap didn't narrow the judge's application of it to the specific forbidden claim — if anything, being more clearly aware of "this case is about hallucinated causation" pushed it to flag the nearest causal-sounding phrase, whichever one it is.

**Verdict, all three: PROMPT AMBIGUITY**, unresolved by the v1.3 fix, for a reason the fix didn't target — these three were never about the *missing* `probes` field the way `coverage`'s issue was hypothesized to be; they're about the anchor's causation ban not being scoped to the specific forbidden claims. Consistent with this session's instruction not to touch that anchor.

---

## 4. cal-06 · ext-a03 · `normalisation` · human 3, judge 1 (new this round)

**Judge's justification:** *"ordered_by and received_by include the job titles when only names were expected, and amounts are given as 8400.00/150.00/8550.00 rather than the requested plain numbers (the trailing .00 is harmless but the inclusion of role text is a normalization issue and the request was for plain numbers with no symbol — trailing .00 on a number is technically not a separator, but the extras on names are a wording deviation from the gold)."*

**Facts:** This case is F1's original item (`open_consistency_flags` in `human_scores.json`, resolved 2026-08-20) — the appended job titles ("Procurement", "Warehouse Supervisor") are exactly the defect F1's rule addresses: *"a value carrying content the gold does not contain scores 2"* under **precision**. The judge scored precision 2 for this, correctly matching both the resolved rule and the human's blind score. It then re-cites the identical job-title issue under `normalisation`, plus a self-contradicting complaint about trailing `.00` on the amounts (its own text hedges mid-sentence: *"technically not a separator, but..."*) — this is the anchor's forbidden double-charge (*"must not be charged twice"*), and the justification's own uncertainty suggests the judge isn't confident in the normalisation complaint on its own merits.

**Verdict: PROMPT AMBIGUITY — the same open precision/normalisation boundary gap flagged in the v1.2-hosted audit (cal-16), now surfacing as a double-charge on a different item rather than a clean human/judge split.** Per this session's explicit instruction, **not resolved this round** — recorded, not touched.

---

## Summary

| # | Item | Dimension | Human | Judge | Verdict |
|---|------|-----------|:---:|:---:|---|
| 1 | cal-14 | faithfulness | 3 | 1 | Prompt ambiguity (causation anchor not scoped to the specific forbidden claim) |
| 2 | cal-14 | coverage | 1 | 3 | Prompt ambiguity (probe now seen, but not cross-referenced to the coverage cap rule) |
| 3 | cal-14 | instruction_adherence | 3 | 1 | Prompt ambiguity (same causation over-read as #1) |
| 4 | cal-06 | normalisation | 3 | 1 | Prompt ambiguity (open precision/normalisation boundary, explicitly not in scope this round) |

**4 of 4 prompt ambiguity, 0 judge incapacity, 0 human error — same qualitative pattern as the v1.2-hosted run, at a lower count.** The `{{PROBES}}` fix is a partial, verifiable win: it demonstrably changed what the judge attends to (visible in cal-14's justifications) and two prior disagreements tightened into the 1-point range, but it didn't fully close cal-14's coverage gap because that requires connecting the probe to a specific rule stated elsewhere in the prompt, which supplying the fact alone didn't guarantee. The remaining four are either a scoping question on the causation anchor or the already-known, deliberately-untouched precision/normalisation boundary — nothing here reads as the judge failing to understand or misreading text in front of it.

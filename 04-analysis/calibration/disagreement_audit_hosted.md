# Disagreement Audit — 20-item calibration, MiniMax-M3 (hosted) vs human, judge_prompt.md v1.2 unchanged

**Required by Scoring-Rubric.md v1.3 §5 rule 4, same as the local-judge audit.** Source: `04-analysis/calibration/agreement_report_hosted.json.big_disagreements` (6 pairs, n=76 dimension-pairs pooled). Judge: `minimax/minimax-m3:free` via GMICloud (ToS-Review.md §5.1b). Prompt version unchanged at v1.2 — this run isolates the effect of the judge model alone, not the prompt.

**Headline: κ = 0.591, AC1 = 0.796, raw agreement 81.6%, 6 ≥2-point disagreements — a large jump from both 7B attempts (0.223, 0.300) but still under the 0.6 gate, and 5 of the 6 gaps sit in one task (summarization), 4 of them on one item (cal-14).** classification, rag-qa and json-output are at or near κ = 1.0.

---

## 1. cal-09 · sum-t10 · `faithfulness` · human 3, judge 1

**Response** (verified against the run file): reports active accounts, revenue, entry-plan share, ticket growth and renewal rate, all numerically correct against gold — but omits the first-response-time degradation (3.1→5.4 hours), the net-growth figure (1,170), and ARPA's actual numbers/cause.

**Judge's justification:** *"The response omits the median first-response time figure... and misses attributing the ARPA drop... leaving key figures out though the numbers stated are accurate."*

**Facts:** The judge's own words concede every stated number is accurate — nothing is invented or contradicted. Faithfulness (rubric §3.1: *"every claim traceable to the source; nothing invented"*) is not the dimension omissions belong to; that's coverage's job, and the judge separately docked coverage 2 (human 3, a 1-point gap, correctly excluded from the ≥2 audit but real) for the *same* omissions. The identical list of missing figures is cited to justify low scores on two different dimensions.

**Verdict: PROMPT AMBIGUITY** — a dimension-boundary bleed, the same class of error as the local judge's citation/groundedness bleed on cal-03 (7B audit #3/#4): no anchor tells this judge that an omission is scored once, under coverage, not charged again as an invented-claim failure under faithfulness.

---

## 2–5. cal-14 · sum-a01 · `faithfulness` (3→0), `coverage` (1→3), `concision` (3→1), `instruction_adherence` (3→1)

**Response:** lists the ticket-volume rise, billing breakdown, and coincident events (pricing launch, renewals, campaign, agent leave), closing: *"two support agents were on leave for the latter half of the month, which **may have contributed** to the higher ticket volume."*

**Judge's `faithfulness` justification:** *"The closing clause... speculates on causation that is not in the source, and combined with the coincident event framing strongly implies a causal link the source explicitly does not establish."*

**Facts:** Gold's `must_not_include` names three specific forbidden claims, all about **the pricing page**: *"the pricing page caused the increase,"* *"the pricing page launch is responsible for the billing tickets,"* *"the increase is due to the new pricing."* The hedged clause the judge flagged is about **agent leave**, not the pricing page, and "may have contributed" is exactly the kind of soft hedge the case's own faithfulness bar (§3.1: contradicted-or-invented claims score 0) doesn't reach — it isn't in the forbidden list, and a plausible, hedged operational claim about staffing isn't the adversarial trap this case tests. **Verdict: PROMPT AMBIGUITY** — the judge generalised a claim-specific prohibition ("don't blame the pricing page") into a blanket ban on any causal language anywhere in the response, which the gold notes don't state.

**`coverage` justification:** *"All key points from the gold reference are present... and all four coincident events."* This is the exact point-counting the coverage anchor forbids (*"never by counting gold points"*), and the exact same miss the local 7B judge made on this identical item (7B audit #9): the case's designed trap — named in the case-level `probes` field, "HALLUCINATION BY INFERENCE" — caps coverage at 1 if missed, but `judge.py` still only assembles `gold.notes` into the prompt, never `probes`, in this hosted run too (the prompt was deliberately kept at v1.2, unchanged, per this session's own instruction). **Verdict: PROMPT AMBIGUITY (confirmed input gap)** — a *stronger* judge hitting the identical failure on the identical item is strong evidence this is the missing-`probes`-field gap identified in the original 7B audit, not a capability ceiling, since a materially more capable model reproduces it exactly.

**`concision` and `instruction_adherence` justifications:** both cite the response's proration/invoice/payment-method breakdown as *"padding... not required at this length"* and the causation language as violating *"the implicit requirement to summarize without inventing causal claims."* The padding claim contradicts the case's own gold: `must_include` explicitly requires *"only 400 of those categorised — mostly proration questions — with 940 uncategorised"* — the exact figures the judge scored down for including. **Verdict: PROMPT AMBIGUITY** — once the judge over-read the causation clause as a violation (above), that single misjudgment appears to have propagated into two more dimensions, and separately, docking concision for content the gold explicitly requires is checkable against the case file, not a matter of interpretation.

**All four of cal-14's disagreements trace to two root causes, both already named in the local-judge audit and unaddressed by design in this run (prompt held at v1.2): the missing `probes` field, and an over-broad reading of a claim-specific faithfulness prohibition.**

---

## 6. cal-16 · ext-h03 · `precision` · human 3, judge 1

**Judge's justification:** *"temperature_setpoint_celsius is 3.9 (should be ~3.3 from 38°F), and distance_km is 512.1 (should be ~824 from 512 miles), both of which are wrong values, not merely formatting issues."*

**Facts, checked against the response:** this is factually correct — verified independently while auditing the local judge's run on the same item (7B audit #10), where the *human* score of `normalisation: 1` already flagged the same two wrong conversions, just under the neighbouring dimension. **This is a real, three-way split on dimension attribution, not a factual disagreement:** human charged the wrong-conversion errors under `normalisation` (rubric §3.2 lists "units" as normalisation's scope) and left `precision` at 3; the hosted judge charges the identical errors under `precision` (its own anchor: *"precision scores whether the value is correct"*) — and **also** re-cites *"temperature and distance conversions are wrong"* in its own `normalisation` justification, docking that dimension too. That is a double-charge the anchor explicitly forbids (*"must not be charged twice"*), even though the judge is the only rater who caught the error under both names.

**Verdict: PROMPT AMBIGUITY** — the anchor distinguishes "canonical form" (normalisation) from "correct value" (precision) but doesn't say which one owns an *arithmetically wrong unit conversion*, which is plausibly either. Both raters are internally consistent and defensible; they're answering a question the rubric doesn't fully resolve. Net positive: the hosted judge caught a real error the human missed under precision specifically — the disagreement is about bookkeeping, not about whether something is wrong.

---

## Summary

| # | Item | Dimension | Human | Judge | Verdict |
|---|------|-----------|:---:|:---:|---|
| 1 | cal-09 | faithfulness | 3 | 1 | Prompt ambiguity (faithfulness/coverage bleed) |
| 2 | cal-14 | faithfulness | 3 | 0 | Prompt ambiguity (over-broad causation reading) |
| 3 | cal-14 | coverage | 1 | 3 | Prompt ambiguity (confirmed: missing `probes` field) |
| 4 | cal-14 | concision | 3 | 1 | Prompt ambiguity (docked for gold-required content) |
| 5 | cal-14 | instruction_adherence | 3 | 1 | Prompt ambiguity (same causation over-read) |
| 6 | cal-16 | precision | 3 | 1 | Prompt ambiguity (precision/normalisation boundary undefined) |

**6 of 6 are prompt/anchor ambiguity, 0 judge incapacity, 0 human error** — a qualitatively different failure pattern than either 7B run, where judge incapacity (factual misreads, hallucinated content) was 3–4 of 10. Every disagreement here traces to a checkable rubric gap, not to the judge misreading what's in front of it. Two of the six (cal-14's coverage, the `probes`-field gap) are the *same named, already-diagnosed* gap from the local-judge audit, reproduced by a materially stronger model — strong evidence that gap is real and judge-independent, not a 7B-specific weakness. This is a real, workable disagreement — not a diffuse capability ceiling — but the prompt was deliberately not touched this session (isolating the judge-switch effect), so it stays a disagreement in this result.

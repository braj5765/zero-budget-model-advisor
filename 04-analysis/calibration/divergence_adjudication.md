# Divergence Adjudication — 6 unadjudicated items from `divergence_list.md`

**Non-blind, post-hoc — a limitation inherent to the exercise, recorded rather than hidden.** This review was conducted by the human scorer (Braj) after seeing both his own original scores and the judge's scores for every item below, using the same protocol as `heldout_human_review.md`. A genuinely blind re-check would require a third, unscored calibration set, which does not exist.

**Bias runs in both directions and was disclosed to the scorer before he answered.** Four of the six items diverge from his own recorded score (cal-18, cal-h17, cal-17 coverage, cal-h15); two diverge from the judge's score while matching his own (cal-09, cal-17 instruction_adherence). He was therefore adjudicating cases where confirming the checklist means admitting his own error, and cases where confirming it means vindicating his own prior score. Neither direction is blind, and neither is free of the incentive that shape implies.

**Correction (2026-09-03):** the paragraph above originally listed cal-17 instruction_adherence in the "diverges from human" group and cal-h15 in the "diverges from judge" group — both backwards. cal-h15 diverges from the human score (2 vs. checklist 3, judge 3) and cal-17 instruction_adherence diverges from the judge score (2 vs. checklist 3, human 3); the text now reads correctly. The aggregate — four diverging from the human scorer, two from the judge — was correct throughout and is what the scorer was told, in that aggregate form, before he answered each item on its own stated reasoning. His verdicts below are unaffected by this correction.

This document records verdicts. It does not change any score, does not recompute κ, and does not touch the rubric, judge prompt, or case files.

---

## 1. cal-18 · in-sample · classification (cls-t07) · ambiguity_handling

**Rule** — `judge_prompt.md` v1.2 classification ANCHOR (not in rubric): *"The optional 'Note:' line is the sanctioned channel for uncertainty; using it where no genuine ambiguity exists costs a point on ambiguity handling."*

**Checklist implies:** 2. **Human recorded:** 3. **Judge recorded:** 2.

**Verdict:** Checklist correct.

**Reasoning (verbatim):** "I missed the point that getting note reduces point by 1 so checklist implied score is right."

---

## 2. cal-h17 · held-out · classification (cls-h03) · ambiguity_handling

**Rule** — Scoring-Rubric.md §3.3 table, 0-cell (base rubric): *"Picks confidently and wrongly with no signal of uncertainty" → 0.*

**Checklist implies:** 0. **Human recorded:** 1. **Judge recorded:** 0.

**Verdict:** Checklist correct.

**Reasoning (verbatim):** "My miss in this case too as directly wrong category was given with no note as well for stating ambiguity"

---

## 3. cal-h15 · held-out · rag-qa (rag-t10) · abstention_calibration

**Rule** — `judge_prompt.md` v1.2 RAG Q&A `{{DIMENSIONS}}`/ANCHOR (not in rubric): *"Answering an ANSWERABLE question correctly is the 3 case, never a deduction..."*

**Checklist implies:** 3. **Human recorded:** 2. **Judge recorded:** 3.

**Verdict:** Checklist incorrect.

**Reasoning (verbatim):** "no checklist is wrong as answer given was straight no but there is not sufficient detail to understand which category refund falls in amongst standard or hardware bundles, but as majority cases it will be no I gave it 2."

---

## 4. cal-09 · in-sample · summarization (sum-t10) · faithfulness

**Rule** — Scoring-Rubric.md §3.1 table (base rubric): *"Faithfulness — 3: Every claim traceable to the source; nothing invented. 0: Contains a claim contradicted by or absent from the source."*

**Checklist implies:** 3. **Human recorded:** 3. **Judge recorded:** 2.

**Verdict:** Checklist correct.

**Reasoning (verbatim):** "checklist and my score is correct as rule meant that what figures are stated are tracable to paragraph given, not whether numbers are missing in summary from paragraph as per reason given by judge"

---

## 5. cal-17 · in-sample · summarization (sum-h03) · coverage

**Rule** — Scoring-Rubric.md §3.1 coverage anchor, v1.4 (base rubric): *"...coverage is 3 where the omitted points are ones the requested length could not accommodate, and 2 where the summary had room and still dropped a substantive point."*

**Checklist implies:** 2. **Human recorded:** 3. **Judge recorded:** 2.

**Verdict:** Checklist correct.

**Reasoning (verbatim):** "I am at fault here by missing the detail by mistake" — confirmed as applying to this dimension.

---

## 6. cal-17 · in-sample · summarization (sum-h03) · instruction_adherence

**Rule** — Scoring-Rubric.md §3.1 table + coverage anchor's double-counting clause, v1.4 (base rubric): *"...marking it down for obeying the length instruction double-counts the same behaviour against instruction adherence, which is its own dimension."*

**Checklist implies:** 3. **Human recorded:** 3. **Judge recorded:** 2.

**Verdict:** Checklist correct.

**Reasoning (verbatim):** "I am at fault here by missing the detail by mistake" — confirmed as applying to this dimension.

---

## Count

**5 of 6: checklist confirmed correct.** Of those five, **3 identify a human scoring error** (cal-18, cal-h17, cal-17 coverage) and **2 identify a judge scoring error** (cal-09, cal-17 instruction_adherence — see correction above; this item's human score of 3 matches the checklist, so confirming the checklist identifies the judge's 2 as the error, not the human's).

**1 of 6: checklist disputed.** cal-h15 — the human scorer maintains his original score (2) against both the checklist's reading and the judge's matching score (3), on the ground that a flat "No" without engaging the hardware-bundle exception does not demonstrate the model actually resolved which category the refund falls into, even though it happens to land on the majority-case answer.

**Correction (2026-09-03):** this section originally read "4 identify a human scoring error... and 1 identifies a judge scoring error (cal-09)," omitting cal-17 instruction_adherence from the judge-error group entirely. Corrected count: 3 human errors, 2 judge errors, matching the corrected bias-disclosure paragraph above.

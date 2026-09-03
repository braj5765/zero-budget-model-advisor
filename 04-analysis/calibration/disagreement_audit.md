# Disagreement Audit — 20-item calibration, qwen2.5:7b vs human, judge_prompt.md v1.0

**Required by Scoring-Rubric.md v1.3 §5, rule 4 ("any ≥2-point disagreement is audited and written up before proceeding, regardless of κ").** Source: `04-analysis/calibration/agreement_report.json.big_disagreements` (10 pairs, n=76 dimension-pairs pooled). Judge justifications are quoted verbatim from `judge_scores.json`. Model responses were pulled from `03-results/run-2026-08-15T114622Z.jsonl` (matched by `case_id` + `run_index==1` + `response_sha256`, same method as `judge.py`) to check the judge's justification against the actual text, not just the score.

Verdict categories, as specified: **prompt ambiguity** (rubric/prompt doesn't give the judge what it needs to score correctly, even in principle), **judge incapacity** (the judge had what it needed and still got the fact wrong), **human error** (the human score is the one that's off).

---

## 1. cal-01 · cls-t08 · `label_validity` · human 3, judge 0

**Response:** `Cancel Subscription\nNote: Report Bug`

**Judge's justification:** *"The response invents a label 'Cancel Subscription' which is outside the permitted label set."*

**Facts:** The instruction states verbatim: *"The permitted labels are exactly: Cancel Subscription, Upgrade Plan, Report Bug, Request Refund, Ask Question."* `Cancel Subscription` is the **first label listed**. It is the wrong label for this bug report (correctly scored 0 on `label_correctness`, no disagreement there), but it is unambiguously a member of the permitted set — the judge's claim it is "outside" that set is false on the text it was just given.

**Verdict: PROMPT AMBIGUITY.** The judge prompt never tells the judge which line of a multi-line response *is* "the label" for scoring purposes — the classification anchor discusses the permitted set and the `Note:` line's role in ambiguity handling, but never states that only line one is evaluated against the permitted set. With `Report Bug` (a real permitted label, and the gold answer) sitting on the second line, the judge appears to have scored some blended reading of the two lines rather than isolating line one before checking set membership — which is consistent with, though not proof of, the justification's flat factual error. This is the motivating case for the v1.2 fix.

---

## 2. cal-02 · rag-t03 · `abstention` · human 3, judge 0

**Response:** `Based on the provided passages, the RX-2C is the only scanner model approved for the cold storage hall.\n\nCitations: P1` — question is answerable from P1; response answers it correctly and cites it correctly.

**Judge's justification:** *"The response confidently answers the question without abstaining, even though it could have used INSUFFICIENT CONTEXT as a token."*

**Facts:** Per rubric §3.4 / the judge prompt's own dimension text, abstention scores 3 for *"says so when the context cannot answer, AND answers when it can."* This question is answerable and the response answers it — exactly the rewarded case. The judge's justification treats "did not emit INSUFFICIENT CONTEXT" as itself a defect, regardless of whether abstention was ever called for.

**Verdict: PROMPT AMBIGUITY.** The dimension is defined as one bidirectional rule ("says so when it can't, AND answers when it can") that the judge must apply after first classifying the question as answerable or not. Qwen2.5:7b is not reliably performing that implicit two-step (classify, then apply the branch) — it appears to apply a single heuristic ("no abstention token → deduct") independent of answerability. Motivates the v1.2 explicit-branch split.

---

## 3. cal-03 · rag-a01 · `groundedness` · human 3, judge 1

**Response:** `INSUFFICIENT CONTEXT\nCitations: P3` — case is genuinely unanswerable (no passage states an erasure timeline); gold's only correct answer is `INSUFFICIENT CONTEXT`.

**Judge's justification:** *"Citations: P3, which does not support an erasure timeline."*

**Facts:** Groundedness asks whether *assertions* in the response are supported by context. The response makes exactly one assertion — `INSUFFICIENT CONTEXT` — which is true and requires no supporting passage. The wrong citation is a real defect, but it belongs to `citation_accuracy` (both human and judge scored that 0 — no disagreement there). The judge charged the same citation error against groundedness too.

**Verdict: PROMPT AMBIGUITY.** The rubric explicitly guards against exactly this kind of double-charging for precision/normalisation (§3.2: *"must not be charged twice"*) but has no equivalent guard telling the judge that a citation defect is `citation_accuracy`'s business only, not groundedness's or answer_correctness's (see #4 below, same case). Not one of the two fixes in scope for v1.2 — flagged for a future anchor, not fixed here.

---

## 4. cal-03 · rag-a01 · `answer_correctness` · human 3, judge 0

**Judge's justification:** *"The response incorrectly cites P3, which does not address erasure timelines."*

**Facts:** The response's answer content, `INSUFFICIENT CONTEXT`, is exactly gold's required answer for this adversarial unanswerable case. The judge's stated reason for scoring 0 is the citation, not the answer — the same dimension-boundary bleed as #3, on the neighbouring dimension.

**Verdict: PROMPT AMBIGUITY.** Same root cause as #3 (no anchor separating citation defects from the dimensions that score assertion content). Not in scope for v1.2.

---

## 5. cal-03 · rag-a01 · `abstention` · human 3, judge 0

**Judge's justification:** *"The response does not abstain when it should, as the context does not provide an erasure timeline."*

**Facts:** The response is `INSUFFICIENT CONTEXT` — the model **did** abstain, using exactly the sanctioned token. The judge's justification asserts the opposite of what is in the response text it was given.

**Verdict: JUDGE INCAPACITY.** This is not a branch-logic problem like #2/#6/#8 below (the judge correctly identifies the case as one where abstention was warranted) — it is a plain misread of what the response says, on a one-line response, with the correct token sitting in it verbatim. No prompt clarification fixes a judge asserting the opposite of the text in front of it. Not addressed by the v1.2 branch split; a capability ceiling, not a wording gap.

---

## 6. cal-07 · rag-h05 · `abstention` · human 3, judge 0

**Response:** correctly answers a supersession question (fourteen rupees/km), correctly cites P2.

**Judge's justification:** *"The response confidently answers the question, which is answerable with the given context."*

**Facts:** The judge's own justification states the fact pattern that should produce a 3 (answerable, answered) — and then scores 0 anyway. Same pattern as #2.

**Verdict: PROMPT AMBIGUITY.** Identical mechanism to #2: the judge appears to score "did not abstain" as a deduction on reflex, even while its own stated reasoning describes the correct behaviour. Motivates the same v1.2 fix as #2.

---

## 7. cal-10 · sum-t09 · `instruction_adherence` · human 3, judge 1

**Response:** *"Our current product recommendation tool calculates suggestions on the fly, which causes severe delays... To fix this, we propose generating recommendations overnight... While this means the suggestions for frequent users will be up to a day old, an alternative approach of simply ignoring older activity proved to hurt the quality..."* — no technical jargon anywhere; `p99`, `embeddings`, and `cache size` are all rewritten into plain language, exactly as the instruction ("Avoid jargon") asks.

**Judge's justification:** *"The response uses unexplained jargon, which is the failure this case probes, and thus scores 1."*

**Facts:** There is no jargon in the response to point to — the justification names the case's *known failure mode* ("this case probes" is language from the case design, not something in the response) rather than anything in the text. The judge's `faithfulness` justification for the same item makes the identical error, calling ordinary phrases like *"massive amounts of past activity"* and *"frequent users"* "unexplained jargon."

**Verdict: JUDGE INCAPACITY.** This reads as the judge scoring the case's intended trap rather than the actual response in front of it — a comprehension failure, not an ambiguity in what "jargon" means. No prompt rewording changes what jargon is or isn't present in a specific response; the judge needs to look at the text and didn't. Not addressed by v1.2.

---

## 8. cal-13 · rag-t04 · `abstention` · human 3, judge 0

**Response:** correctly answers the two-branch deviation-reporting question, correctly cites P1.

**Judge's justification:** *"The response confidently answers the question without abstaining."*

**Verdict: PROMPT AMBIGUITY.** Same mechanism as #2 and #6 — the fourth and last instance of this exact pattern, all four occurring on rag-qa's `abstention` dimension, none scattered elsewhere. This is the clearest signal in the whole audit that the fix belongs in the abstention dimension's wording, not in four unrelated response-reading failures.

---

## 9. cal-14 · sum-a01 · `coverage` · human 1, judge 3

**Response:** lists ticket-volume increase, billing-question breakdown, and several coincident events (pricing page launch, renewals, re-engagement campaign, agent leave) without directly asserting the pricing page *caused* the increase — but also without explicitly flagging that causation is *not* established, which is what gold's notes require for full marks: *"Explicitly noting that causation is not established scores 3."*

**Judge's justification:** *"The response captures all key points identified in the gold reference, including the ticket volume increase, the largest category of increase, and the categorization of billing tickets."*

**Facts:** This is exactly the point-counting approach the coverage anchor (rubric §3.1, carried verbatim into the judge prompt) explicitly forbids: *"Coverage is judged by significance and against the length the instruction permits — never by counting gold points."* The case's designed probe — stated in the case file's `probes` field as *"HALLUCINATION BY INFERENCE — source invites a causal conclusion it does not state"* — is what coverage must be capped against per the anchor's own rule (*"If the point the case was designed to probe... is missed, coverage caps at 1"*). `judge.py`'s prompt assembly passes `gold.notes` to the judge but never the case-level `probes` field, so the judge was never shown the sentence that names this as *the* probed point in the first place — it had to infer the cap rule's target from `gold.notes`' more general phrasing alone.

**Verdict: PROMPT AMBIGUITY** — specifically an **input gap**: the judge cannot apply an anchor rule that depends on identifying "the probed point" when the field naming that point (`probes`) is never assembled into its prompt. Confirmed as a known implementation gap in `PROJECT-STATE.md`'s 2026-08-28 entry. **Out of scope for the v1.2 edit requested this session** (which is restricted to the abstention split and the classification label-line fix) — recorded here so it isn't lost, and is a candidate for a v1.3 prompt change or a `judge.py` fix.

---

## 10. cal-16 · ext-h03 · `normalisation` · human 1, judge 3

**Response:** `distance_km: 512.1` (gold: 824.0 — 512 miles never converted to km, just relabeled); `temperature_setpoint_celsius: 3.9` (gold: 3.3–3.4 — arithmetic doesn't match a correct conversion of the stated 38°F, nor of the 41°F trap value the case is designed to catch); `delivery_window_start: "2026-03-03"` (gold: "2026-03-05" — the source states the window explicitly as mm-dd-yyyy "03-05-2026 to 03-07-2026").

**Judge's justification:** *"Dates, numbers, units, and names are in the requested canonical form, with appropriate rounding."*

**Facts:** Two of the four numeric conversions in the response are wrong by amounts that are trivial to check against the source (512 vs 824 km is not a rounding difference; 3.9°C is not within the case's own stated 3.3–3.4°C tolerance). The judge's justification asserts the opposite without showing any check against the source values.

**Verdict: JUDGE INCAPACITY.** This is an arithmetic-verification failure, not a reading-comprehension or rubric-wording issue — the case's own gold notes spell out the trap (*"converting [41°F] instead is a precision failure"*) and the anchor is unambiguous about what's expected. A 7B local model appears not to reliably re-derive or check unit conversions against the source numbers before scoring. Not addressed by v1.2; a capability ceiling, and a candidate reason (alongside #7) to try 14b if a sharpened 7b still misses per rubric §5's own escalation order.

---

## Summary

| # | Item | Dimension | Human | Judge | Verdict |
|---|------|-----------|:---:|:---:|---|
| 1 | cal-01 | label_validity | 3 | 0 | Prompt ambiguity |
| 2 | cal-02 | abstention | 3 | 0 | Prompt ambiguity |
| 3 | cal-03 | groundedness | 3 | 1 | Prompt ambiguity |
| 4 | cal-03 | answer_correctness | 3 | 0 | Prompt ambiguity |
| 5 | cal-03 | abstention | 3 | 0 | Judge incapacity |
| 6 | cal-07 | abstention | 3 | 0 | Prompt ambiguity |
| 7 | cal-10 | instruction_adherence | 3 | 1 | Judge incapacity |
| 8 | cal-13 | abstention | 3 | 0 | Prompt ambiguity |
| 9 | cal-14 | coverage | 1 | 3 | Prompt ambiguity (input gap, out of scope this pass) |
| 10 | cal-16 | normalisation | 1 | 3 | Judge incapacity |

**7 prompt ambiguity, 3 judge incapacity, 0 human error.** No human score in this set of 10 was found to be the one that's wrong on re-examination against the source text and gold.

Of the 7 prompt-ambiguity items, 4 (#2, #5*, #6, #8) sit on rag-qa's `abstention` dimension — *`#5 differs in kind (a factual misread, not a branch-logic failure) and is verdicted judge incapacity, but it's grouped here as it shares the same failing dimension.* 4 of 4 abstention disagreements share the identical mechanism ("did not abstain" scored as a deduction independent of whether abstention was warranted), which is the strongest, most concentrated signal in this audit and the basis for the v1.2 fix (split into explicit answerable/unanswerable branches, dimension renamed).

`#1` (classification label-line boundary) is the second v1.2 fix. `#3`/`#4` (citation-error bleed into neighbouring dimensions) and `#9` (missing `probes` field) are real, named gaps left unaddressed this pass, by the session's own scope restriction — not because they're any less real than the two that were fixed.

---

## v1.2 re-judge outcome (qwen2.5:7b, same 20 items)

Full results in `agreement_report_v1.2.json`. n_ge2_disagreements dropped **10 → 7**, quadratic-weighted κ rose **0.223 → 0.300**, Gwet's AC1 **0.756 → 0.768**, raw agreement **77.6% → 78.7%**. Still fails the κ ≥ 0.6 gate, and ≥2-point disagreements remain, so per rubric §5's own table this is still **real disagreement, not eligible for a prevalence-artifact reading** — the fix worked partially, not fully.

**Per-item outcome against the two fixes:**

- **cal-02, cal-07 (abstention branch split): fixed.** Both now score `abstention_calibration: 3` with justifications that correctly name the branch ("does not need to state INSUFFICIENT CONTEXT", "Answers an ANSWERABLE question correctly") — the systematic "no token → deduct" reflex from v1.0 is gone on these two.
- **cal-03 (abstention branch split): not fixed, as predicted.** Still scores `abstention_calibration: 0` with the justification *"The response gives an answer instead of stating INSUFFICIENT CONTEXT"* — factually false; the response is `INSUFFICIENT CONTEXT\nCitations: P3`, unchanged from v1.0. Confirms the #5 verdict (judge incapacity, not a wording gap): the branch split doesn't fix a judge that misreads the response text itself.
- **cal-13 (abstention branch split): turned into a new failure mode, not a fix.** The judge now returns `abstention_calibration: "n/a"` with justification *"Not applicable as the question is answerable."* This is a rubric §3.6 rule 1 violation — a judge may never mark a dimension `n/a` at its own discretion, and `rag-t04`'s gold carries no `n/a` designation (human scored it 3). `agreement.py` correctly excludes it as a protocol violation rather than silently treating it as agreement or disagreement, but it means the branch split introduced a new, unintended escape hatch: describing two branches gave the judge room to read "this case doesn't need the INSUFFICIENT CONTEXT check" as "score n/a" rather than "score the ANSWERABLE branch: 3." **Not fixed in this pass** — a v1.3 candidate is an explicit line telling the judge n/a is never a valid answer for this dimension, only 0 or 3.
- **cal-01 (classification label-line fix): not fixed.** Still scores `label_validity: 0`, justification now *"The response 'Cancel Subscription' is not a member of the permitted label set"* — near-identical to v1.0's wording, and still false (it's the first label named in the instruction). The prompt clarification about which line is "the label" had no effect, because the failure was never about line-boundary confusion — it's a flat factual misread of the permitted-set text, i.e. **judge incapacity**, not the prompt ambiguity this audit tentatively credited it as. Revises the #1 verdict in light of the re-judge: this one belongs with #5, #7, #10 (judge incapacity) rather than with the abstention group.

**Revised verdict tally after re-judge evidence:** of the 10 v1.0 disagreements, 2 (cal-02, cal-07) are resolved; cal-01 is reclassified from prompt-ambiguity to judge-incapacity now that the targeted fix demonstrably didn't move it; cal-03 (3 dimensions), cal-10, cal-16 remain judge-incapacity as before; cal-14 remains an unaddressed input gap; and cal-13 is a new protocol violation rather than a disagreement. **Net: 4 confirmed judge-incapacity items, 2 unaddressed input/anchor gaps (cal-03's groundedness/answer_correctness bleed, cal-14), 1 new protocol violation (cal-13), 2 fixed.** No item in either pass was human error.

# Known Limitations

This is the honest account of what could be wrong with this index, ordered by how much each item should change a reader's confidence — strongest first, not by when I found it. This document is a decision, not a promise being paid: Rubric §8 never committed to writing it. I wrote it because "what did you get wrong" is a fair question to ask of a benchmark, and it deserves a better answer than a scattered set of caveats across four files.

Every item below states what happened, why, what it does and doesn't invalidate, and what would fix it. I don't state a limitation without its consequence — a caveat that changes nothing a reader does with the numbers is decoration, not disclosure.

---

## 1. The judge calibration arc

This is the most serious limitation in the project, and the most interesting, because it's not a story about a benchmark being sloppy — it's a story about what a well-designed control (pre-registration, held-out measurement, blinded scoring) still can't buy you at this scale.

### 1.1 The gate cleared, then failed to generalise

The κ gate is Rubric §5's condition for trusting an LLM judge instead of hand-scoring everything: quadratic-weighted Cohen's κ ≥ 0.6 against human scores. It cleared at **κ = 0.650**, in-sample, after four rounds of prompt iteration (`judge_prompt.md` v1.1 → v1.2 → a judge-model swap → v1.3) — all four rounds run against the *same* 20 calibration items (`calibration/sample.json`).

`JUDGE-RUN-PLAN.md` §6 pre-registered, before scoring a single held-out item, how a fresh measurement would be read. Held-out κ on 20 fresh items — drawn by `case_id` exclusion from the 80 case_ids untouched by the in-sample set, matched to the in-sample set's adversarial task composition so the two numbers are comparable — came in at **κ = 0.358** (AC1 0.689, raw agreement 72.6%, 7 disagreements of ≥2 points, n=73 pooled pairs). That falls in §6's pre-registered `< 0.45` band: *"the in-sample gate does not hold; κ=0.650 is invalidated as a generalisation estimate."*

**I'm stating this without softening it: the index ships with a judge whose agreement with a careful human is unestablished.** The in-sample 0.650 was real, but it was measured on the same 20 items the prompt had been tuned against four times — an optimistically biased estimate by an amount this project never had a clean way to size until the held-out draw existed. The collapse is not uniform: classification held at κ=0.96 and extraction/summarization collapsed to κ=0.08/0.06, with json-output returning κ=0.00 despite 12/13 raw agreement — the concentrated-marginal paradox Rubric v1.3 pre-registered a reading procedure for. **This invalidates the specific claim "the judge agrees with a careful human at κ=0.65."** It does not, by itself, mean every judged score in the production run is wrong — §1.3 below is why that distinction matters and why I didn't just re-score everything by hand in response.

### 1.2 The number itself is not a clean measure of judge quality

Two things undercut κ as an instrument here, independent of what it measured.

**The specification gap.** `Scoring-Checklist.md` §9 — built as a pure restatement of Rubric §3, then swept against `judge_prompt.md` and every case file's `conventions` block in both directions — found 13 rules that governed the judge's scoring throughout the entire run and were never written into the rubric at all: 4 in classification (the first-line label convention, the `Note:` line's status, the hedging deduction, the "however reasonable the reading" qualifier), 5 in RAG Q&A (the dimension rename, the two-branch abstention procedure, the `INSUFFICIENT CONTEXT` token, the citation line format, the empty-`supported_by` rule), 2 in json-output (key order is never scored, null-vs-omitted-key), and 2 more in extraction and out-of-scope territory (canonical-form definitions and a related undecided trailing-decimal case). Rubric §5 step 1 requires the human to hand-score "working from this rubric only." **The two legs — human and judge — were never scored against the same specification, in-sample or held-out.** κ in this pipeline was never cleanly measuring judge-vs-human agreement; it was partly measuring the gap between two documents both of us believed were "the rubric."

**The protocol asymmetry.** The in-sample 20 were hand-scored in one long blind session that surfaced cross-item inconsistencies I logged as flags F1/F2 — those became Rubric v1.4's coverage and precision anchors, and scoring them forced re-reads across items. The held-out 20 were scored in a guided walkthrough with zero notes recorded and no cross-item consistency pass, because nothing required one. An unknown share of the κ drop from 0.650 to 0.358 may measure that protocol difference rather than judge generalisation. This is a hub design error, not a scorer error, and it means 0.358 is not a clean estimate of overfitting either — it's a number produced by two different instruments pointed at two different specs, reported as if they were the same measurement.

**What this does and doesn't invalidate:** it means the gap between 0.650 and 0.358 overstates pure overfitting by some amount I can't size. It does not mean the true generalisation number is good — §1.4 shows independently that a large share of the held-out disagreements are real human error, not judge error, which cuts the other way.

### 1.3 κ measures concordance, not correctness — demonstrated, not asserted

This is the sharpest finding in the project, and it comes from the project's own data rather than a textbook caveat about weighted kappa.

`cal-h11` (`ext-h05`, `null_handling`) is determinate under Rubric §3.2's v1.1 anchor: *"nulling a determinable value scores 1."* No ambiguity, no open boundary — §3.8.2 confirms the ambiguity there attaches to recall, not to null handling. The human scored it **3**. The judge scored it **0**. **Both wrong, in opposite directions, on a rule that has been unambiguous since v1.1.**

Had both of us said 3, κ would have recorded perfect agreement on that pair — and both scores would still have been wrong. **κ measures whether two raters land on the same number, not whether that number is correct.** This is exactly why validating scores against the standard — the checklist, applied item by item — turned out to be the better instrument than the κ gate: it compares each score to the rule, not the raters to each other. The full checklist sweep (`divergence_list.md`) found 15 divergences across both calibration sets this way, 2 of them (`cal-09`, `cal-17` instruction_adherence) sourced to the base rubric itself rather than the judge-only §9 rules — meaning the checklist caught real judge errors on rules the human also had, which is what makes it more than a laundering device for the judge's own prompt.

**Consequence:** any reader treating κ=0.650 (or 0.358) as "the judge is X% as good as a human" is reading the statistic wrong on this project's own evidence. The correct reading is narrower: this many pairs landed on the same number, and a meaningful fraction of the ones that didn't — and some that did — are traceable to a specific, nameable cause below.

### 1.4 Four failure modes, none of them visible to κ

1. **The human misses a rule the rubric never carried.** `heldout_human_review.md` confirms 5 of 5 presented cases (`cal-h01` parseability, three dimensions of `cal-h05`, `cal-h12` coverage) as scoring errors where the case's own `gold.notes` or a file-level convention stated the rule plainly and I read the response generously without checking it.
2. **The judge confuses dimension boundaries.** `cal-09` scored faithfulness 2 for an *omission* — faithfulness (Rubric §3.1) is about invented or contradicted claims, not missing ones; that's coverage's job. `cal-17` deducted instruction_adherence for the identical omission already (correctly) charged to coverage on the same item — the exact double-counting the coverage anchor's own text warns against.
3. **The judge prompt cannot represent a real case shape.** §3.8.3: the abstention-calibration branch is binary (UNANSWERABLE/ANSWERABLE) and has no representation for a conditionally answerable question. `cal-h15` (`rag-t10`, "yes if a hardware bundle, no otherwise") lands on the majority-case answer without resolving the condition and scores 3 under the binary read. I disputed this on adjudication and held my score of 2 against both the checklist and the judge — recorded as open, not resolved, because the defect is in a rule the judge was given that the rubric never carried at all.
4. **Both raters miss a determinate rule at once.** `cal-h11`, above — the case that shows κ's blind spot directly.

None of these four is visible in a κ number by construction — a concordance statistic cannot distinguish "both raters agree because both are right" from "both raters agree because both share the same blind spot," and it actively hides case 4 as if it were a success.

---

## 2. Everything else, in descending order of how much it should move your confidence

### 2.1 Half the scoring scale is discretion, not anchor

Rubric §3's dimension tables anchor only the 3 and 0 poles on most dimensions — a clean pass and a clean failure. The 1s and 2s in between are not separately anchored. This is where essentially all of the *non*-determinate disagreement in the calibration data lives: `divergence_list.md` explicitly set aside a population of ordinary 1-vs-2 "by degree" gaps (concision and instruction_adherence length judgments, partial-credit coverage without a named probed point) as non-determinate by design, not as checklist gaps. **Consequence:** a 1-vs-2 disagreement between any two scorers on this rubric is expected noise, not a defect to chase — but it also means roughly half the scale's resolution is judgment calls rather than rule application, on every dimension that isn't pinned at both ends. **Fix:** anchor the 1 and 2 cells the way v1.4 anchored coverage and precision — from calibration intuition, before the next run, not after seeing scores.

### 2.2 Three declared open boundaries, and six extraction gaps sit inside the first two

Rubric §3.8 declares three boundaries this rubric does not resolve: precision/normalisation (§3.8.1), recall/normalisation/null-handling (§3.8.2), and conditional answerability (§3.8.3). `divergence_list.md`'s complete sweep found **six** extraction-task gaps that sit inside the first two of these — `cal-06`, `cal-11`, `cal-16`, `cal-h11` (normalisation), `cal-h14` under §3.8.1, and `cal-h11`'s recall under §3.8.2 — meaning the open boundary isn't a one-off edge case, it's the seam extraction hits repeatedly whenever a field carries both a content defect and a canonical-form defect. **Consequence:** any extraction score close to a dimension boundary on precision/normalisation/recall should be read as sitting in genuinely undecided territory, not as a scoring error. **Fix:** the boundaries stay open per instruction — resolving one now, after seeing which reading is more flattering to which model, is exactly the move this project's own freeze discipline exists to prevent. They're candidates for the next rubric freeze, before the next run.

### 2.3 One person did all the human scoring

Every hand-score in this project — calibration, held-out, adjudication — was scored by me, the same person who wrote the rubric, authored the test cases, and wrote the gold references. There is no inter-human reliability estimate anywhere in this project; I cannot tell you whether a second qualified scorer would agree with me at a rate anywhere near what would make the judge's agreement-with-me figure meaningful. **Consequence:** every "human score" in every file should be read as "this project's author's score," not as a proxy for scorer consensus. **Fix:** this is structurally unfixable at this project's scale (see §3) — it would require recruiting and calibrating a second scorer, which is a different project.

### 2.4 Both adjudications were non-blind by necessity, and one had a disclosure error

`heldout_human_review.md` and `divergence_adjudication.md` both had me review my own prior scores after seeing the judge's scores and, in the second case, after being told the aggregate split (4 diverging from me, 2 from the judge) before ruling item by item. Both documents disclose this themselves — a genuinely blind re-check would need a third, unscored calibration set, which doesn't exist. `divergence_adjudication.md` additionally had a bias-disclosure paragraph that listed two items backwards (`cal-17` instruction_adherence and `cal-h15` swapped between the "diverges from human" and "diverges from judge" groups) — the aggregate counts told to me before I answered were correct throughout, so my verdicts stand, but the error was in a document meant to demonstrate the review wasn't gamed, and it shipped with a mistake in exactly that section before being caught and corrected in place. **Consequence:** treat every adjudication verdict as "confirmed by the interested party, with the stated caveats," not as independent confirmation. **Fix:** none available inside this project — same structural limit as §2.3.

### 2.5 Rubric v1.4's anchors were articulated after seeing what needed explaining

The coverage and precision anchors added in v1.4 were written from the scoring intuitions that the first blind calibration session exposed (flags F1/F2), not derived in advance of scoring anything. The changelog states this plainly and it's legitimate under this project's own freeze discipline only because it happened **before any judge output existed** — no judged score influenced the anchor, and both anchors reproduced every score already recorded rather than requiring a re-score. **Consequence:** these two anchors are calibration-derived rather than first-principles-derived. That's a legitimate way to build a rubric, but it means their generality beyond this project's specific 20-case calibration set is unverified. **Fix:** none needed unless a future run finds a case the anchor handles badly — then it gets amended and logged the same way, pre-run.

### 2.6 Everything after 2026-08-19 is an in-file claim, not a git-attested one

`git log` runs to `e33d7cd` (2026-08-19). Every amendment, revert, and pre-registration dated after that — Rubric v1.3 through v1.8, `JUDGE-RUN-PLAN.md` §4b's four dated re-judge sessions, §6's pre-registration table and no-v1.4 pre-commitment, both held-out audits, both adjudications — was committed in one batch on 2026-09-03. I'm not softening this: a reader who doesn't trust the in-file dates has no independent way to check, from the repository alone, that v1.3 was really written before v1.4, that §4b's same-day amend-then-revert really happened the same day, or that §6's pre-registration really predated any held-out item being scored. The discipline itself — writing the response before seeing the number, freezing a prompt before a run, reverting an amendment whose premise failed — was followed either way; what's missing is a third party's ability to verify the *order* from git rather than from my word. **Consequence:** every pre-registration claim in this project rests on trusting the author for a three-week window. **Fix:** none, retroactively — the work is done. Going forward, commit each amendment as it happens rather than batching.

### 2.7 n=20 per task, and adversarial sub-scores rest on n=3

Differences under roughly 5 points on the 0–100 scale are not claimed as meaningful anywhere in this index. Adversarial sub-scores — the slice designed to actually separate models — rest on n=3 per task and are directional signal, not measurement. **Consequence:** don't read a 3-point gap between two models on any table as a real difference, and read every adversarial sub-score as "this is where I'd look first," not "this is the number." **Fix:** more cases per task; blocked on the same time/budget constraint that set n=20 in the first place.

### 2.8 OpenRouter's exclusion is not random

OpenRouter was cut from quality scoring after 96/300 successful calls (68% `RATE_LIMIT`) — not enough coverage to support median-of-three at the 12/5/3 stratification. The exclusion correlates with availability under load, which is exactly the property this index claims to measure. **Consequence:** the four scored providers are, by construction, the four that were available enough to score — a selection effect baked into which providers get a quality number at all, not just a footnote about one excluded provider. **Fix:** none within a zero-budget design; a paid tier or a longer collection window would remove the constraint that produced the cut, but both are out of scope by the project's own thesis.

### 2.9 Untuned prompts undersell a model that responds to tuning

Every model got the identical, untuned prompt (Decision B4), deliberately — the goal is out-of-the-box behaviour, which is what the audience actually experiences. **Consequence:** a model that would perform substantially better with light prompt engineering scores as if it can't, and this index has no way to distinguish "this model is bad at the task" from "this model needs a different prompt to be good at the task." **Fix:** none without abandoning the design's central comparability claim — per-model tuning would measure my prompt engineering, not the model.

### 2.10 Temperature 0 is not deterministic, and every summarization figure inherits it

Median-of-three assumes run-to-run stability temperature 0 doesn't actually provide. Measured median-identical rates on summarization ranged **36–60%** across the four scored models (Groq 36.2%, Gemini 58.8%, Mistral 60.0%, Ollama 45.0%) — meaning on well over a third of summarization cases, the three runs judged didn't even produce the same output, let alone the same score. **Consequence:** every summarization quality figure in this index carries meaningfully more run-to-run variance than the "temp 0, median-of-three" framing implies, and this is the task where it's worst — summarization is also the task where in-sample and held-out κ collapsed hardest, and this is very likely part of why. **Fix:** none free; more runs per case would tighten the median at proportional cost, and providers that don't honor temp=0 exactly (a known property of some inference stacks) aren't going to change that behaviour for a free-tier caller.

### 2.11 Derived token ceilings are projections, not vendor figures

Mistral's request-equivalent ceilings (e.g. ~65,198 req/day for extraction) are computed from this benchmark's own measured mean tokens-per-request against Mistral's documented 1B-tokens/month cap — not a number Mistral publishes. The conversion assumes a 30-day month and this benchmark's specific prompt lengths; a builder with longer prompts than this benchmark's extraction cases will hit the ceiling sooner than the published number suggests, and the figure moves if Mistral's documented monthly cap changes. **Consequence:** treat every Mistral "requests/day" figure in this index as this-benchmark's-workload-shaped, not as a general Mistral capacity claim. **Fix:** none needed beyond stating the derivation, which the summary table already does — the number is only ever meant to be a translation aid, not a vendor fact.

### 2.12 The judge pass itself had a ~3% silent-retry failure rate, concentrated where judging is hardest

The production judge pass ran through shared-pool contention: of 1,200 judged keys, 95 were retried, and 39 of those retries followed a `MALFORMED` result — a judge-content failure (the judge produced output that didn't parse as a score), not a transport failure. That means roughly 3% of recorded production judgments are the *surviving* attempt of a judge call that first produced unusable output, and those 39 concentrate in exactly the slice this document has already flagged as hardest to judge: 13 in summarization, 16 in Ollama's outputs (the model whose long, meandering completions are hardest for the judge to parse cleanly). **Consequence:** for summarization and Ollama specifically, a nontrivial share of scores come from a second attempt after a first one failed outright — not evidence those second attempts are wrong, but a reason to hold slightly less confidence in exactly the two slices already shown (§1.1, §2.10) to be the least reliable. **Fix:** none applied retroactively; a future run could log and publish the first (failed) attempt alongside the retry for full transparency, which this run didn't do.

### 2.13 The n/a exclusion rule flatters Mistral's JSON score

Mistral's json-output score of 33.8 is computed with 39 of 60 dimension-rows excluded as `n/a` (parseability failed, so the other three dimensions never get scored, per §3.6's aggregation rule). Excluding a failure from the denominator rather than scoring it 0 raises the mean over what a "did it actually work" reading would show. **Consequence:** 33.8 is the *charitable* number — it's the average of the roughly one-third of attempts that produced parseable JSON, not a score that reflects the two-thirds that didn't. The success rate and n/a count are published beside it for exactly this reason; read them together, not the quality score alone. **Fix:** none — this is the correct application of Rubric §3.6's rule, stated here so nobody mistakes 33.8 for "how often Mistral produces usable JSON."

### 2.14 The test cases encode one person's view of a typical workload

The 12/5/3 typical/hard/adversarial split, and what counts as "typical" within it, reflects my own judgment about what an ordinary builder asks an LLM to do across these five tasks. Someone with a different workload profile in mind would design different cases and could reasonably get different results. **Consequence:** this index measures performance on *this* test design, not on "everyday tasks" in some universal sense. **Fix:** the cases and golds are published specifically so this can be checked and disagreed with — that's the intended remedy, not a rubric or scoring change.

### 2.15 Free tiers are a moving target

Every figure in this index — rate limits, quality scores, latency — is a point-in-time reading, dated at the top of every table. Providers change free-tier terms, models, and infrastructure without notice. **Consequence:** treat any figure more than a quarter old as unverified. **Fix:** the quarterly refresh cadence exists specifically to bound this; there's no way to make a free-tier snapshot durable beyond re-measuring it.

---

## 3. What the next refresh fixes, and what stays broken

**Fixed by the next quarterly run.** The set of 20 items originally drawn for a third calibration round ("Set 3") was dropped this cycle (`PROJECT-STATE.md` §8, 2026-09-03) — not discarded, redirected. It becomes the next quarterly refresh's calibration set, judged under Rubric v1.8's consolidated specification (the 13 rules now written into §3.3–§3.5) on both legs for the first time. That run will produce a κ figure that is an actual test of whether v1.8 closed the spec gap described in §1.2, rather than another number asserted to be better. If it clears 0.6 held-out under the consolidated spec, the judge-agreement claim in this document gets to change; if it doesn't, that's a real finding about this judge model rather than a documentation problem.

**Structurally unfixable at this project's scale.** Two things in this document don't go away with better documentation or a better prompt: a single human scorer (§2.3) and n=20 per task (§2.7). Both are functions of this being a zero-budget, single-author project, not defects in this run specifically — fixing either means a different project, with a second scorer and a larger case budget, not a better rubric.

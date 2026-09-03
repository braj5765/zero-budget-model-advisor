# Scoring Rubric — Zero-Budget Model Advisor

**Version 1.8 · Frozen 2026-08-10 · Amended 2026-08-11, 2026-08-19, 2026-08-20, 2026-08-28 (×3, one reverting another), 2026-08-28 pre-aggregation, and 2026-09-03 (documentation only) · Author: Braj**

This rubric was written and frozen **before any model was run**. That ordering is deliberate: a rubric authored after seeing results can be shaped, consciously or not, to fit them. Any change after freeze is recorded in the changelog at the end, with a reason, and any affected results are re-scored — not patched.

---

## 1. What this rubric scores, and what it doesn't

**In scope:** output quality only — the correctness and usability of what the model returned.

**Out of scope, measured separately and never folded into the quality score:** latency, rate-limit ceiling, cost, and availability. Those are operational facts; mixing them into a quality number would make a slow-but-accurate model indistinguishable from a fast-but-wrong one, which is exactly the tradeoff the advisor exists to expose.

**Refusals and errors are not quality failures.** A refusal, timeout, rate-limit rejection, or malformed response is logged as a **failure mode** with its own taxonomy (§6) and excluded from the quality mean, with the failure rate reported alongside every score. A model that answers 60% of the time excellently and refuses 40% must not appear equal to one that answers everything well.

---

## 2. Scoring scale

Every dimension is scored **0–3**. Four points, no midpoint, forced discrimination.

| Score | Meaning |
| :---- | :---- |
| **3** | Fully correct. A competent practitioner would ship this unchanged. |
| **2** | Correct in substance, minor flaw. Usable after a trivial edit. |
| **1** | Materially flawed. Contains an error a user would have to catch and fix. |
| **0** | Unusable or wrong in a way that would mislead the user. |

Deliberately no 1–5 or 1–10 scale: finer scales invite false precision and inflate judge variance without adding signal. Deliberately no even-point midpoint: "3 out of 5" is where ambiguous cases go to hide.

---

## 3. Dimensions by task

Each task is scored on 3–4 dimensions. Task score = **unweighted mean of its dimensions**, normalised to 0–100. Unweighted because any weighting scheme I invent is an unargued assumption about what a builder cares about; the advisor lets the *user* weight dimensions at query time instead.

### 3.1 Summarization

| Dimension | 3 | 0 |
| :---- | :---- | :---- |
| **Faithfulness** | Every claim traceable to the source; nothing invented | Contains a claim contradicted by or absent from the source |
| **Coverage** | Captures all key points identified in the gold reference | Misses the primary point of the source |
| **Concision** | Within the requested length; no padding or restatement | Substantially over length, or mostly filler |
| **Instruction adherence** | Honours format, length, tone and audience as instructed | Ignores the instruction |

***Coverage is judged by significance and against the length the instruction permits — never by counting gold points.*** *If the point the case was designed to probe (its `probes` field, or the point named in `gold.notes`) is missed, **coverage caps at 1** however many other points landed. If the probed point lands, coverage is **3** where the omitted points are ones the requested length could not accommodate, and **2** where the summary had room and still dropped a substantive point. The length clause is load-bearing: a three-sentence summary cannot carry five gold points, and marking it down for obeying the length instruction double-counts the same behaviour against instruction adherence, which is its own dimension.*

### 3.2 Extraction

| Dimension | 3 | 0 |
| :---- | :---- | :---- |
| **Precision** | No extracted field is wrong or hallucinated | Majority of fields wrong or fabricated |
| **Recall** | All fields present in the source were extracted | Most present fields missed |
| **Normalisation** | Dates, numbers, units, names in the requested canonical form | Raw or inconsistent forms throughout |
| **Null handling** | Absent fields returned as null, **and determinable fields resolved rather than nulled** | Fabricates plausible values for absent fields, **or nulls fields the source does determine** |

*Null handling is scored separately because guessing a missing field is a distinct and more dangerous failure than missing a present one — it is silent.*

***Over-abstention is scored here too, and symmetrically.*** *A model that returns null for everything it finds slightly awkward is not being careful, it is being useless — and it would otherwise score perfectly on a dimension called "null handling". Fabrication scores 0; nulling a determinable value scores 1. The asymmetry is deliberate: inventing a value misleads silently, while over-nulling merely under-delivers, and the rubric should say which it considers worse.*

***Precision scores whether the value is correct, not how it is worded.*** *A semantically equivalent rewording of the correct value scores **3**. A value carrying content the gold does not contain scores **2** — the field is not the requested value and a consumer must edit it — or lower where that content is not in the source at all, which is fabrication. Differences of canonical form (date format, unit, casing, separators) are **normalisation's** business, not precision's, and must not be charged twice.*

### 3.3 Classification

| Dimension | 3 | 0 |
| :---- | :---- | :---- |
| **Label correctness** | Matches the gold label | Wrong label |
| **Label validity** | Output is a member of the permitted label set | Invents a label outside the set |
| **Ambiguity handling** | On deliberately ambiguous cases, flags or picks the defensible label | Picks confidently and wrongly with no signal of uncertainty |

*Correctness and validity are separated because a model that returns "Somewhat Positive" when the set is {Positive, Negative, Neutral} has broken the integration, not just the answer.*

***Output format — v1.8, documenting a rule operative since the case files were authored and since `judge_prompt.md` v1.2, never previously written here.*** *The label is the first line of the response, and only the first line: label correctness and label validity are checked against that line alone. An optional second line beginning "Note:" is the sanctioned channel for uncertainty — it is never itself the label, must not be read as an alternate answer, and its content must not be checked against the permitted label set. A label outside the permitted set scores 0 on label validity regardless of how defensible the reading is. Using the "Note:" line where no genuine ambiguity exists costs a point on ambiguity handling.*

### 3.4 RAG Q&A

| Dimension | 3 | 0 |
| :---- | :---- | :---- |
| **Groundedness** | Every assertion supported by the supplied context | Asserts facts not in the context |
| **Answer correctness** | Factually answers the question asked | Wrong answer |
| **Abstention calibration** | Says so when the context cannot answer, **and answers when it can** | Confidently answers a question the context cannot support — **or refuses a question the context does support** |
| **Citation accuracy** | Points to the passage that actually supports the claim | Cites a passage that does not support it |

*Abstention has its own dimension and its own test cases (§4). A model that never says "I don't know" is a specific, common, and expensive failure — it must be visible in the score, not averaged away. **The mirror failure is scored on the same dimension:** a model that abstains on answerable questions would otherwise game this dimension by refusing everything. Test sets must therefore pair each unanswerable case with answerable cases that look superficially similar, or the dimension measures caution rather than judgment.*

***Abstention calibration mechanics and citation format — v1.8, documenting rules operative since `judge_prompt.md` v1.2, never previously written here.*** *Renamed from "Abstention" to "Abstention calibration" to match the name every judge score has carried since v1.2 — this rubric had not been updated to match. Scoring proceeds in two steps: first decide, from the gold answer alone, whether the case is UNANSWERABLE or ANSWERABLE; then apply only that branch's rule. Answering an ANSWERABLE question correctly is the 3 case on this dimension, never a deduction, regardless of what answer correctness separately scores. The sanctioned abstention signal is the literal string INSUFFICIENT CONTEXT; citations appear on a final line of the form "Citations: P1, P3", or "Citations: none" when abstaining. Where a case's supporting-passage list is empty, no answer should have been given, and citing any passage is a citation-accuracy failure regardless of what it says. See §3.8.3 for a branch this two-way split does not represent.*

### 3.5 Structured JSON output reliability

| Dimension | 3 | 0 |
| :---- | :---- | :---- |
| **Parseability** | Parses on first attempt, no wrapper prose or fences | Fails to parse |
| **Schema conformance** | All required keys present, types correct, no extra keys | Violates the schema |
| **Enum/constraint conformance** | Constrained values respected | Values outside the permitted set |
| **Content correctness** | Values are factually right | Values wrong |

*Parseability is scored before content: an unparseable response scores 0 on parseability and its content dimensions are not scored, since a broken response has no content to judge. This is recorded so the failure is attributed correctly.*

***Key order and nullable-key handling — v1.8, documenting rules operative since the case files were authored, never previously written here.*** *Key order is never scored — JSON objects are unordered, and scoring order would measure a serialisation incidental, not correctness. Where a key is declared nullable, it must be present with a JSON null value; omitting the key entirely is a schema conformance failure, not a null-handling matter — this task carries no null-handling dimension.*

### 3.6 Not-applicable dimensions, and how scores aggregate

Some cases cannot be scored on every dimension of their task. An unparseable JSON response has no content to judge (§3.5). A classification case where **no permitted label is correct** cannot be scored on label correctness — the model cannot be right, and recording that as a miss would punish it for a property of the test, not of the model, while still leaving label validity and ambiguity handling fully measurable.

**Rules:**

1. A dimension may be marked `n/a` **only where the case design makes it unscoreable**, and the case's `gold.notes` must say which dimensions are `n/a` and why. A judge may never mark `n/a` at its own discretion.
2. **`n/a` is excluded from the denominator**, not scored zero. A case scoring 3 and 2 on its two applicable dimensions scores the same as a three-dimension case scoring 3, 2 and their mean.
3. **Case score** = mean of applicable dimensions → normalised to 0–100.
4. **Task score** = unweighted mean of the 20 case scores. Not a mean of dimension means — that would let a task with many `n/a` dimensions weight cases unevenly without anyone noticing.
5. **All 20 cases count toward the task score**, adversarial included, and the three adversarial cases are *additionally* reported as their own sub-score. They are not double-counted; the sub-score is a lens on the same data.
6. Every published task score carries its **`n/a` count**. A model accumulating `n/a` marks through unparseable output is not doing well, and the count is what makes that visible.

### 3.7 Median-of-three — at which level, and how `n/a` interacts

Pinned 2026-08-28, **before any aggregation was computed**. v1.6 restored median-of-three but did not say whether the median is taken over dimension scores or over case scores. `/scoring` cannot guess, and the two give different answers.

1. **The median is taken per dimension, across the three runs.** Dimensions are the unit of measurement and §3.6's aggregation chain begins there, so the median feeds that chain unchanged: median per dimension → case score (mean of applicable dimensions) → task score (mean of case scores).
2. **`n/a` is not a number and never participates in a median.** For a dimension across three runs: if **two or more runs are `n/a`**, the dimension is `n/a` for that case. Otherwise take the median of the numeric runs only, and record how many runs contributed.
3. **Report the spread, don't discard it.** For every dimension, record the min–max across the three runs alongside the median. Median-of-three exists to blunt nondeterminism; the spread is what tells a reader how much nondeterminism there was, and with all three runs judged it is now measurable on every case rather than a subsample. Publish per-task median spread beside every task score.

*Rule 3 recovers the one thing the withdrawn v1.5 amendment was going to give us. Median-of-three alone hides variance; median plus published spread reports it.*

*Rule 6 exists because `n/a` is the one mechanism here that could quietly flatter a bad model — excluding a dimension raises the mean. Publishing the count is what keeps the exclusion honest.*

### 3.8 Open scoring boundaries — declared, not resolved (v1.8)

Three boundaries between dimensions are not fully specified by this rubric. They are declared here rather than left to be resolved by accident by whoever scores next, per the same discipline that governs everything else in §3: a boundary this rubric doesn't decide should not quietly get decided anyway.

**3.8.1 Precision / Normalisation (extraction).** The precision anchor (§3.2) says a canonical-form-only defect belongs to normalisation and must not be charged twice. It does not fully specify, for a field carrying both extra content and a canonical-form deviation, which dimension owns which part of the defect. **Open.**

**3.8.2 Recall / Normalisation / Null handling (extraction).** Where a field is present and determinable in the source but the response returns `null` for it instead of extracting it, null handling (§3.2) scores this 1 (over-abstention). Whether the same miss should also reduce recall, or whether a related formatting complaint on an adjacent field belongs to normalisation rather than recall, is not addressed anywhere in §3.2. **Open.**

**3.8.3 Conditional answerability (RAG Q&A).** The abstention-calibration branch (§3.4) is binary — UNANSWERABLE or ANSWERABLE — and has no representation for a question the context answers only conditionally (e.g. "yes, if it's a hardware bundle; no otherwise"). A response that lands on the majority case without resolving the condition scores 3 under the binary branch as currently specified. Disputed on adjudication (`04-analysis/calibration/divergence_adjudication.md`, item 3): the human scorer holds this does not demonstrate the model resolved anything, and declined to accept the binary reading over his own recorded score. Unlike §3.8.1 and §3.8.2, this defect lives in a rule the judge was given (`judge_prompt.md` v1.2) that this rubric never carried at all until this amendment. **Open.**

---

## 4. Test case design

**~20 cases per task, 100 total.** Each task's set is stratified so that a model can't win by being good at the easy half:

- **~12 typical cases** — representative of ordinary builder workloads.
- **~5 hard cases** — long inputs, noisy or contradictory sources, unusual formats.
- **~3 adversarial cases** — designed to induce the specific failure the task is prone to: unanswerable RAG questions, extraction sources with fields genuinely absent, classification inputs sitting on a category boundary, JSON requests with nested or constrained schemas.

The adversarial slice is where free tiers actually separate, and it is reported as its own sub-score, not just folded into the mean.

Each case carries: input, task instruction, **gold reference** (expected output or acceptable-answer criteria), difficulty tier, and the failure it is designed to probe. Cases and golds are published with the index.

**Fixed conditions across all models:** identical prompts (no per-model prompt tuning — that measures my prompt engineering, not the model), temperature 0 where supported, same system prompt, same context, three runs per case. **Judging scope amended 2026-08-28, before the production judge pass — see §4b.**

### 4b. Judged scope — amended 2026-08-28, then REVERTED the same day, both pre-production-run

**Current rule: median-of-three stands as originally specified. The judge scores all three runs — 1,200 responses.**

*Amendment (2026-08-28, morning):* judging was to be limited to `run_index = 1` (400 responses) with a 10% three-run subsample for variance, on the stated ground that 1,200 responses were "not executable within available free-tier throughput." That figure came from a CPU-only local judge at ~6 minutes per response — roughly 120 hours.

*Reverted (2026-08-28, same day, before any production judging beyond a 20-row timed cluster):* the hosted judge measured **4.4 seconds per response** — an 80× difference. A 1,200-response pass is approximately **90 minutes plus retry overhead**, not 120 hours. **The premise of the amendment was false, so the amendment goes.**

Retaining a scope reduction whose stated justification has been falsified by my own measurement would be indefensible under challenge — the honest position is that the constraint was real when measured against one judge and disappeared when the judge changed. Amendments are reverted when their premise fails, not kept because they are convenient.

**Consequence, and it is an improvement:** median-of-three is restored *and* run-to-run variance becomes measurable across every case rather than a 10% subsample. Both the original guarantee and the better diagnostic, for about two hours of wall clock.

*Residual risk, disclosed:* no daily cap has been observed in ~60 calls, but the cap is genuinely unverified above that. The pass is resumable and append-only, so a cap costs a resumption, not a re-run.
---

## 5. Judging protocol

**Hybrid: LLM-as-judge over the full set, calibrated against a human-scored subset.**

1. **Human calibration set.** I hand-score **20% of cases (20 total), stratified across all five tasks and all three difficulty tiers**, working from this rubric only, before seeing any judge output.
2. **Judge runs the full set** — all 100 cases × all models — scoring each dimension 0–3 against the gold reference, and required to output a one-sentence justification per dimension. Justifications are published; a score without a reason is not auditable.
3. **Agreement check.** Judge vs human scores on the calibration set are compared using **quadratic-weighted Cohen's κ**. Threshold: **κ ≥ 0.6**.
   - κ ≥ 0.6 → judge scores stand for the remaining 80%.
   - κ < 0.6 → the judge is not trusted for that task. Either the rubric anchors are sharpened and the whole set re-judged, or that task is scored entirely by hand. Which path was taken is reported.
4. **Disagreement audit.** Every case where judge and human differ by ≥2 points is inspected and written up. These are the most informative cases in the whole benchmark and go into the methodology writeup.

### Reading κ when the human marginal is concentrated — pre-registered 2026-08-19, before any judge run

The human calibration scores came in at **89% 3s**. Quadratic-weighted κ is chance-corrected, so when one rater's marginal distribution is that concentrated, expected agreement converges on observed agreement and κ becomes small and unstable — the judge could match on nearly every item and still land under 0.6. This is the well-documented kappa paradox, not a property of the judge.

The response is fixed **now, before any judge output exists**, because deciding how to read a disappointing κ after seeing it is the post-hoc shaping this rubric's freeze discipline exists to prevent.

**Always reported together, never κ alone:** the full confusion matrix, both raters' marginal distributions, exact raw agreement, the count of ≥2-point disagreements, and **Gwet's AC1** (which is stable under skewed marginals where κ is not).

**Decision rule:**

| Condition | Reading | Action |
| :---- | :---- | :---- |
| κ ≥ 0.6 | Judge agrees | Proceed to the full set |
| κ < 0.6, **and** AC1 ≥ 0.6, **and** zero ≥2-point disagreements, **and** disagreements not concentrated in one task or dimension | Prevalence artifact, not judge failure | Extend the calibration set with **10 additional hard/adversarial items** and recompute. Do **not** lower the threshold |
| κ < 0.6 and AC1 < 0.6 | Real disagreement | Sharpen anchors, re-judge, per §5 |
| Any ≥2-point disagreement | Real disagreement regardless of κ | Audit and write up before proceeding |

**The threshold never moves.** The only sanctioned remedy for a prevalence artifact is *more discriminating data* — hard and adversarial items where scores should legitimately vary — because that attacks the cause. Lowering the gate would attack the evidence.

**Root cause, stated for publication:** a calibration sample stratified by task, tier and model is not necessarily stratified by *judgment difficulty*. Items where competent raters would plausibly differ are what make an agreement statistic informative, and they were not deliberately over-sampled. This belongs in Known Limitations regardless of the κ result.

### Judge independence — the conflict of interest, stated plainly

The judge must not be a model under test. Scoring Gemini's output with Gemini invites self-preference bias, which is documented and real. **The judge is a model outside the benchmark set**, and its identity, version and date are recorded with every score.

The unavoidable residual risk: judge models have their own stylistic preferences and may systematically favour outputs resembling their own. The κ check against human scores is the control on this, and it is the reason the human subset exists at all rather than being a formality. **Judge model version is pinned per index release**; a judge version change invalidates cross-release comparison and forces a re-run.

### Blinding and order effects

Model identity is stripped from responses before judging. Response order is randomised per case. Both are cheap and remove two known confounds.

---

## 6. Failure mode taxonomy

Logged per call, reported per model per task as a rate, never mixed into quality:

| Code | Failure |
| :---- | :---- |
| `RATE_LIMIT` | Rejected for quota/rate reasons |
| `TIMEOUT` | No response within the task's timeout window |
| `REFUSAL` | Model declined to attempt the task |
| `TRUNCATION` | Output cut off mid-response |
| `MALFORMED` | Response unparseable for a task requiring structure |
| `EMPTY` | Empty or whitespace-only response |
| `API_ERROR` | Provider-side error (5xx, auth, capacity) |
| `HALLUCINATION` | Confident assertion unsupported by source — scored 0 *and* logged, as it is both a quality and a trust failure |

---

## 7. Reporting rules

Every published model-task result carries, together and never separately:

- Quality score (0–100) with the per-dimension breakdown
- Adversarial sub-score
- Success rate and the failure-mode distribution
- p95 latency and the measured rate-limit ceiling
- n, judge model + version, and judging date

**No composite "overall best model" ranking is published.** The whole thesis is that the right choice depends on the user's volume, latency SLA and quality bar — a single leaderboard number would contradict the product.

---

## 8. Known limitations

Stated up front rather than waiting to be found:

- **n = 20 per task** is small. Differences under ~5 points on the 0–100 scale are not claimed as meaningful. Adversarial sub-scores rest on n=3 and are directional signal, not measurement.
- **My test cases encode my judgment** of what a typical builder workload looks like. Published so others can disagree specifically.
- **Judge bias is mitigated, not eliminated.** κ against 20 human-scored cases is a real control but a modest one.
- **Free tiers are moving targets.** Every result is a point-in-time reading, dated at the top of every table.
- **Prompts are not model-tuned.** This measures out-of-the-box behaviour, which is what the audience actually experiences — but a model that responds well to tuning is undersold here. Stated, not hidden.

---

## 9. Changelog

| Version | Date | Change | Reason |
| :---- | :---- | :---- | :---- |
| 1.0 | 2026-08-10 | Initial freeze, pre-run | — |
| 1.8 | 2026-09-03 | **Documentation amendment only.** Writes into §3.3, §3.4 and §3.5 the rules that were already operative in `classification.json`'s, `rag-qa.json`'s and `json-output.json`'s `conventions` blocks and in `judge_prompt.md` v1.2–v1.3's per-task anchors throughout the run, but had never been written into this rubric: classification's first-line/`Note:`-line mechanics and the "however reasonable the reading" qualifier (§3.3); RAG's two-branch abstention procedure, the `INSUFFICIENT CONTEXT` token, the `Citations:` line format, and the empty-`supported_by` rule (§3.4); json-output's key-order and nullable-key rules (§3.5). Renames RAG's `Abstention` dimension to `Abstention calibration` (§3.4), matching every judge score since `judge_prompt.md` v1.2 — the rubric had not been updated to match. Adds §3.8, declaring three open scoring boundaries (precision/normalisation, recall/normalisation/null-handling, and conditional answerability) rather than resolving them. | This documents rules that were already operative in the case files and the judge prompt throughout the run; it changes no scoring standard. `01-rubric-and-testcases/Scoring-Checklist.md` §9's sweep found nothing in rubric §3 that `judge_prompt.md` and the case files did not already carry, and nothing here was invented to close a gap. It reproduces every recorded score across all four calibration files (`human_scores.json`, `judge_scores_hosted_v1.3.json`, `human_scores_heldout.json`, `judge_scores_heldout.json`) **except the six divergences adjudicated in `04-analysis/calibration/divergence_adjudication.md`** — three confirmed human scoring error (cal-18, cal-h17, cal-17 coverage), two confirmed judge scoring error (cal-09, cal-17 instruction adherence), and one left open on dispute (cal-h15, now §3.8.3). A post-run change to this rubric is legitimate only on that basis — that it documents what already governed scoring rather than changing it — per this rubric's own freeze discipline (preamble: "Any change after freeze is recorded in the changelog... with a reason, and any affected results are re-scored — not patched") and consistent with §4b's own precedent that an amendment stands or falls on whether its stated premise holds, not on convenience. |
| 1.7 | 2026-08-28 | **Added §3.7** — median-of-three is taken **per dimension** across runs, `n/a` never enters a median (2+ `n/a` runs ⇒ dimension is `n/a`), and min–max spread is recorded and published beside every median. | v1.6 restored median-of-three without specifying the level at which it applies; dimension-level and case-level medians give different answers and `/scoring` cannot guess. Pinned **before any aggregation was computed**, so no score influenced the choice. |
| 1.6 | 2026-08-28 | **Reverted v1.5's §4b scope reduction.** Median-of-three restored; the judge scores all 1,200 responses. | v1.5 cut judged scope on the ground that 1,200 responses were not executable. A timed cluster on the hosted judge measured 4.4s/response against the 6min/response local figure the estimate was built on — ~90 minutes, not ~120 hours. The premise was false, so the amendment was withdrawn rather than kept. Reverted the same day, before any production judging beyond a 20-row cluster; those 20 rows are `run_index = 1` and belong to the full manifest either way, so nothing is wasted or re-run. |
| 1.5 | 2026-08-28 | **Added §4b — judged scope.** Judge scores `run_index = 1` only (400 responses); run-to-run variance measured on a 10% three-run subsample rather than by median-of-three across the whole set. Benchmark execution is unchanged; this is a judging-scope change. | Judging 1,200 responses is not executable within available free-tier throughput. Amended after the κ gate cleared (0.650) but **before the production pass began**, so no judged production result influenced it, and the calibration set — judged on `run_index = 1` throughout — is unaffected. |
| 1.4 | 2026-08-20 | **Two anchors added, both to dimensions that were under-specified where they touch a neighbouring dimension.** §3.1 **Coverage** — judged by significance and against the permitted length, never by counting gold points: missing the probed point caps coverage at 1; if the probed point lands, 3 where omissions were forced by the length instruction and 2 where the summary had room. §3.2 **Precision** — scores whether the value is correct, not how it is worded: equivalent rewording 3, value carrying content absent from the gold 2, content absent from the source lower; canonical-form differences belong to normalisation and are not charged twice. | Both gaps surfaced as cross-item inconsistencies during blind human calibration on 2026-08-20 (flags F1 and F2 in `human_scores.json`) and are recorded there with the resolving rule. **Stated plainly, because it matters to how this should be read: the rules were articulated from the scoring intuitions the calibration exposed, not derived in advance — the human judgments are the data, and the rules are what makes them reproducible by a judge.** Both anchors reproduce the scores already recorded, so **no calibration item was re-scored**; had either rule required a revision, the affected items would have been re-scored before the model map was unsealed, since a score revised after seeing model identity is no longer blind. Amended **before any judge output existed**. The judge prompt must carry both anchors verbatim — an anchor the human applies that the judge cannot see manufactures disagreement that reads as judge error. |
| 1.3 | 2026-08-19 | **Added §5 subsection on reading κ under a concentrated marginal.** Requires confusion matrix, both marginals, raw agreement, ≥2-point disagreement count and Gwet's AC1 alongside κ; fixes a four-way decision rule; sanctions extending the calibration set with hard/adversarial items as the only remedy for a prevalence artifact. Threshold unchanged at 0.6. | Human calibration returned 89% 3s. Under that skew κ is unstable and can read low despite near-total agreement — a known property of the statistic, not of the judge. Amended **before any judge output existed**, so no result influenced the rule; deciding this after seeing a low κ would have been indistinguishable from rescuing a failed gate. |
| 1.2 | 2026-08-11 | **Added §3.6** — not-applicable dimensions and the aggregation rule: `n/a` excluded from the denominator rather than scored zero, case score = mean of applicable dimensions, task score = mean of case scores, all 20 cases counted with adversarial additionally broken out, and `n/a` count published alongside every score. | v1.0 defined how dimensions combine into a case score but never how case scores combine into a task score — `/scoring` could not be built from it unambiguously. The `n/a` concept already existed implicitly (§3.5 leaves content dimensions unscored on unparseable output) but had no aggregation rule, and classification case `cls-a02` made a second instance explicit. Amended **pre-run**; no results affected. |
| 1.1 | 2026-08-11 | **Over-abstention made an explicit failure** on two dimensions: Extraction §3.2 null handling (nulling a determinable field scores 1) and RAG Q&A §3.4 abstention (refusing an answerable question scores 0). Added the requirement that unanswerable cases be paired with superficially similar answerable ones. | Gap surfaced while authoring extraction cases: v1.0 anchored both dimensions only on the fabrication side, so a model that returned null or "I don't know" universally would have scored full marks on them. Amended **pre-run**, with no results affected — the freeze exists to prevent post-hoc tuning to observed results, not to prevent fixing a defect before any data exists. Had this surfaced after the run, the correct action would have been re-scoring, not amendment. |

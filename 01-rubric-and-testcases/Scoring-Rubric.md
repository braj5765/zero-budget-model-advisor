# Scoring Rubric — Zero-Budget Model Advisor

**Version 1.2 · Frozen 2026-08-10 · Amended 2026-08-11, pre-run · Author: Braj**

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

### 3.2 Extraction

| Dimension | 3 | 0 |
| :---- | :---- | :---- |
| **Precision** | No extracted field is wrong or hallucinated | Majority of fields wrong or fabricated |
| **Recall** | All fields present in the source were extracted | Most present fields missed |
| **Normalisation** | Dates, numbers, units, names in the requested canonical form | Raw or inconsistent forms throughout |
| **Null handling** | Absent fields returned as null, **and determinable fields resolved rather than nulled** | Fabricates plausible values for absent fields, **or nulls fields the source does determine** |

*Null handling is scored separately because guessing a missing field is a distinct and more dangerous failure than missing a present one — it is silent.*

***Over-abstention is scored here too, and symmetrically.*** *A model that returns null for everything it finds slightly awkward is not being careful, it is being useless — and it would otherwise score perfectly on a dimension called "null handling". Fabrication scores 0; nulling a determinable value scores 1. The asymmetry is deliberate: inventing a value misleads silently, while over-nulling merely under-delivers, and the rubric should say which it considers worse.*

### 3.3 Classification

| Dimension | 3 | 0 |
| :---- | :---- | :---- |
| **Label correctness** | Matches the gold label | Wrong label |
| **Label validity** | Output is a member of the permitted label set | Invents a label outside the set |
| **Ambiguity handling** | On deliberately ambiguous cases, flags or picks the defensible label | Picks confidently and wrongly with no signal of uncertainty |

*Correctness and validity are separated because a model that returns "Somewhat Positive" when the set is {Positive, Negative, Neutral} has broken the integration, not just the answer.*

### 3.4 RAG Q&A

| Dimension | 3 | 0 |
| :---- | :---- | :---- |
| **Groundedness** | Every assertion supported by the supplied context | Asserts facts not in the context |
| **Answer correctness** | Factually answers the question asked | Wrong answer |
| **Abstention** | Says so when the context cannot answer, **and answers when it can** | Confidently answers a question the context cannot support — **or refuses a question the context does support** |
| **Citation accuracy** | Points to the passage that actually supports the claim | Cites a passage that does not support it |

*Abstention has its own dimension and its own test cases (§4). A model that never says "I don't know" is a specific, common, and expensive failure — it must be visible in the score, not averaged away. **The mirror failure is scored on the same dimension:** a model that abstains on answerable questions would otherwise game this dimension by refusing everything. Test sets must therefore pair each unanswerable case with answerable cases that look superficially similar, or the dimension measures caution rather than judgment.*

### 3.5 Structured JSON output reliability

| Dimension | 3 | 0 |
| :---- | :---- | :---- |
| **Parseability** | Parses on first attempt, no wrapper prose or fences | Fails to parse |
| **Schema conformance** | All required keys present, types correct, no extra keys | Violates the schema |
| **Enum/constraint conformance** | Constrained values respected | Values outside the permitted set |
| **Content correctness** | Values are factually right | Values wrong |

*Parseability is scored before content: an unparseable response scores 0 on parseability and its content dimensions are not scored, since a broken response has no content to judge. This is recorded so the failure is attributed correctly.*

### 3.6 Not-applicable dimensions, and how scores aggregate

Some cases cannot be scored on every dimension of their task. An unparseable JSON response has no content to judge (§3.5). A classification case where **no permitted label is correct** cannot be scored on label correctness — the model cannot be right, and recording that as a miss would punish it for a property of the test, not of the model, while still leaving label validity and ambiguity handling fully measurable.

**Rules:**

1. A dimension may be marked `n/a` **only where the case design makes it unscoreable**, and the case's `gold.notes` must say which dimensions are `n/a` and why. A judge may never mark `n/a` at its own discretion.
2. **`n/a` is excluded from the denominator**, not scored zero. A case scoring 3 and 2 on its two applicable dimensions scores the same as a three-dimension case scoring 3, 2 and their mean.
3. **Case score** = mean of applicable dimensions → normalised to 0–100.
4. **Task score** = unweighted mean of the 20 case scores. Not a mean of dimension means — that would let a task with many `n/a` dimensions weight cases unevenly without anyone noticing.
5. **All 20 cases count toward the task score**, adversarial included, and the three adversarial cases are *additionally* reported as their own sub-score. They are not double-counted; the sub-score is a lens on the same data.
6. Every published task score carries its **`n/a` count**. A model accumulating `n/a` marks through unparseable output is not doing well, and the count is what makes that visible.

*Rule 6 exists because `n/a` is the one mechanism here that could quietly flatter a bad model — excluding a dimension raises the mean. Publishing the count is what keeps the exclusion honest.*

---

## 4. Test case design

**~20 cases per task, 100 total.** Each task's set is stratified so that a model can't win by being good at the easy half:

- **~12 typical cases** — representative of ordinary builder workloads.
- **~5 hard cases** — long inputs, noisy or contradictory sources, unusual formats.
- **~3 adversarial cases** — designed to induce the specific failure the task is prone to: unanswerable RAG questions, extraction sources with fields genuinely absent, classification inputs sitting on a category boundary, JSON requests with nested or constrained schemas.

The adversarial slice is where free tiers actually separate, and it is reported as its own sub-score, not just folded into the mean.

Each case carries: input, task instruction, **gold reference** (expected output or acceptable-answer criteria), difficulty tier, and the failure it is designed to probe. Cases and golds are published with the index.

**Fixed conditions across all models:** identical prompts (no per-model prompt tuning — that measures my prompt engineering, not the model), temperature 0 where supported, same system prompt, same context, three runs per case with the median score taken to blunt nondeterminism.

---

## 5. Judging protocol

**Hybrid: LLM-as-judge over the full set, calibrated against a human-scored subset.**

1. **Human calibration set.** I hand-score **20% of cases (20 total), stratified across all five tasks and all three difficulty tiers**, working from this rubric only, before seeing any judge output.
2. **Judge runs the full set** — all 100 cases × all models — scoring each dimension 0–3 against the gold reference, and required to output a one-sentence justification per dimension. Justifications are published; a score without a reason is not auditable.
3. **Agreement check.** Judge vs human scores on the calibration set are compared using **quadratic-weighted Cohen's κ**. Threshold: **κ ≥ 0.6**.
   - κ ≥ 0.6 → judge scores stand for the remaining 80%.
   - κ < 0.6 → the judge is not trusted for that task. Either the rubric anchors are sharpened and the whole set re-judged, or that task is scored entirely by hand. Which path was taken is reported.
4. **Disagreement audit.** Every case where judge and human differ by ≥2 points is inspected and written up. These are the most informative cases in the whole benchmark and go into the methodology writeup.

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
| 1.2 | 2026-08-11 | **Added §3.6** — not-applicable dimensions and the aggregation rule: `n/a` excluded from the denominator rather than scored zero, case score = mean of applicable dimensions, task score = mean of case scores, all 20 cases counted with adversarial additionally broken out, and `n/a` count published alongside every score. | v1.0 defined how dimensions combine into a case score but never how case scores combine into a task score — `/scoring` could not be built from it unambiguously. The `n/a` concept already existed implicitly (§3.5 leaves content dimensions unscored on unparseable output) but had no aggregation rule, and classification case `cls-a02` made a second instance explicit. Amended **pre-run**; no results affected. |
| 1.1 | 2026-08-11 | **Over-abstention made an explicit failure** on two dimensions: Extraction §3.2 null handling (nulling a determinable field scores 1) and RAG Q&A §3.4 abstention (refusing an answerable question scores 0). Added the requirement that unanswerable cases be paired with superficially similar answerable ones. | Gap surfaced while authoring extraction cases: v1.0 anchored both dimensions only on the fabrication side, so a model that returned null or "I don't know" universally would have scored full marks on them. Amended **pre-run**, with no results affected — the freeze exists to prevent post-hoc tuning to observed results, not to prevent fixing a defect before any data exists. Had this surfaced after the run, the correct action would have been re-scoring, not amendment. |

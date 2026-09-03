# Scoring Checklist — restatement of Scoring-Rubric.md v1.7

**Not a new rubric. A restatement.** §§0–8 extract every rule verbatim or near-verbatim from Scoring-Rubric.md §2–§3.7's tables and italicised anchor paragraphs, reordered into explicit decision sequences. No rule in §§0–8 resolves an ambiguity the rubric leaves open, and none was invented to fill a gap. Where the rubric doesn't decide something, this checklist says so and stops — see §8 (Open boundaries).

Each rule in §§0–8 cites its source clause. If a line there has no citation, it should not be there.

**§9 is a different kind of content and is marked as such.** It consolidates rules that were operative throughout the run — enforced by the case files' `conventions` blocks and by `judge_prompt.md` v1.3's per-task anchors — but were never written into the rubric itself. Rubric §5 step 1 requires the human scorer to work "from this rubric only," so §9's rules governed the judge's scoring and never governed the human's. §9 is not a restatement of the rubric; it is sourced to the case file and prompt clause it actually comes from, and is clearly out of scope for the "cite the rubric clause" discipline that governs §§0–8.

---

## 0. Universal preconditions

**0a. `n/a` check — rubric §3.6 rule 1, before every dimension.**
Before scoring any dimension: does this case's `gold.notes` state that this dimension is `n/a` for this case, and why? If yes → record `n/a`, stop, do not score. **A scorer may never decide `n/a` on their own judgement** — only where the case design itself makes the dimension unscoreable, per the case's own notes.

**0b. Scale — rubric §2.**
Every dimension: 0, 1, 2, or 3. No midpoint.
- **3** — Fully correct. A competent practitioner would ship this unchanged.
- **2** — Correct in substance, minor flaw. Usable after a trivial edit.
- **1** — Materially flawed. Contains an error a user would have to catch and fix.
- **0** — Unusable or wrong in a way that would mislead the user.

---

## 1. Summarization — rubric §3.1

**1.1 Faithfulness**
1. Is every claim in the response traceable to the source? → if yes, 3.
2. Does the response contain a claim contradicted by, or absent from, the source? → 0.
3. Otherwise (traceable but imprecisely stated, or a minor unsupported flourish that isn't a factual claim) → 1 or 2 by degree; rubric gives no finer anchor than the 3/0 poles.

**1.2 Coverage — rubric §3.1 table + anchor (v1.4)**
1. Identify the point this case was designed to probe: the case's `probes` field, or the point named in `gold.notes`.
2. Did the response miss that probed point? → **coverage caps at 1**, regardless of how many other points landed. Stop.
3. Did the probed point land? Continue:
   a. Were the omitted (non-probed) points ones the requested length could not accommodate? → **3**.
   b. Did the summary have room and still drop a substantive point? → **2**.
4. Coverage is judged by significance against the length the instruction permits — **never by counting gold points**. Do not mark a summary down for omissions forced by the length instruction; that is instruction-adherence's business, not coverage's, and double-charging it here double-counts the same behaviour.

**1.3 Concision**
1. Is the response within the requested length, with no padding or restatement? → 3.
2. Is the response substantially over length, or mostly filler? → 0.
3. Between those: minor overrun or minor padding → 1 or 2 by degree.

**1.4 Instruction adherence**
1. Does the response honour format, length, tone, and audience as instructed? → 3.
2. Does it ignore the instruction? → 0.
3. Between: a single honoured-but-imperfect axis (e.g. right length, slightly off tone) → 1 or 2 by degree.
4. Do not re-penalise here a length shortfall already charged to coverage (§1.2 rule 4) — that is double-counting the same behaviour.

---

## 2. Extraction — rubric §3.2

**2.1 Precision — rubric §3.2 table + precision anchor (v1.4)**
1. Is the extracted value semantically correct, regardless of wording? → **3**, even if reworded.
2. Does the value carry content the gold does not contain? → **2** — the field is not the requested value and a consumer must edit it.
3. Is that extra content not present in the source at all (i.e. invented, not just reworded from elsewhere in the source)? → **lower than 2** — this is fabrication.
4. Is the *only* defect a difference of canonical form (date format, unit, casing, separators)? → **do not charge precision** — that is normalisation's business (§2.3), and charging both dimensions for the same defect double-counts it.
5. Majority of fields wrong or fabricated → **0**.

**2.2 Recall — rubric §3.2 table**
1. Were all fields present in the source extracted? → 3.
2. Were most present fields missed? → 0.
3. Between: some present fields missed → 1 or 2 by degree.
4. **Open boundary — see §8.2:** the rubric does not say whether a field that *was* present and determinable, but was returned as `null` instead of extracted, counts against recall, against null handling (§2.4), or only the latter. Do not resolve this here; if it arises, flag it rather than picking a side.

**2.3 Normalisation — rubric §3.2 table**
1. Are dates, numbers, units, and names in the requested canonical form throughout? → 3.
2. Are they raw or inconsistent throughout? → 0.
3. **Open boundary — see §8.1:** where a value carries extra (non-canonical-form) content already charged under precision (§2.1 rule 2), the rubric's anchor says a canonical-form defect "must not be charged twice" against both dimensions — but does not fully specify which defects on a single field count as "canonical form" (normalisation's business) versus "wrong content" (precision's business) when the two blur on the same field. Do not resolve this here.

**2.4 Null handling — rubric §3.2 table + null-handling anchor (v1.1) + over-abstention anchor**
1. Does the response fabricate a plausible value for a field the source does not state? → **0**. This is also logged as `HALLUCINATION` per rubric §6.
2. Does the response return `null` (or otherwise refuse to resolve) a field the source *does* determine? → **1**. This is over-abstention: symmetric to fabrication, scored less harshly because it under-delivers rather than silently misleading.
3. Are absent fields correctly returned as `null`, and determinable fields correctly resolved? → **3**.
4. The asymmetry (fabrication = 0, over-nulling a determinable field = 1) is deliberate and explicit — apply it as stated, not by degree.

---

## 3. Classification — rubric §3.3

**3.1 Label correctness**
1. Does the label match the gold label? → 3.
2. Is the label wrong? → 0.
(No finer anchor in the rubric — this dimension is binary in practice.)

**3.2 Label validity**
1. Is the output a member of the permitted label set stated in the instruction? → 3.
2. Does it invent a label outside that set? → 0, "however reasonable the reading" is not a rubric phrase for this dimension but follows directly from §3.3's own framing: label correctness and validity are scored separately *because* an out-of-set label breaks the integration, not just the answer.

**3.3 Ambiguity handling**
1. Is this a deliberately ambiguous case? Flags or picks the defensible label → 3.
2. Does the response pick confidently and wrongly with no signal of uncertainty? → 0.
3. Between: a defensible pick with excess or insufficient hedging → 1 or 2 by degree.

---

## 4. RAG Q&A — rubric §3.4

**4.1 Groundedness**
1. Is every assertion in the response supported by the supplied context? → 3.
2. Does it assert facts not in the context? → 0.

**4.2 Answer correctness**
1. Does the response factually answer the question asked? → 3.
2. Is the answer wrong? → 0.

**4.3 Abstention — rubric §3.4 table + anchor (v1.1)**
1. Determine, from the gold answer alone, which branch this case is in:
   - **Unanswerable** — the context cannot answer.
   - **Answerable** — the context can answer.
2. If unanswerable: did the response say so? → 3. Did it confidently answer anyway? → 0.
3. If answerable: did the response give the answer? → 3. Did it refuse ("cannot be determined" or equivalent) a question the context *does* support? → 0.
4. This dimension is symmetric by design — a model that never abstains and a model that always abstains must not both score well here. Score only the branch that applies to this case; a correct answer to an answerable question is never a deduction.

**4.4 Citation accuracy**
1. Does the citation point to the passage that actually supports the claim? → 3.
2. Does it cite a passage that does not support it? → 0.

---

## 5. Structured JSON output reliability — rubric §3.5

**5.1 Parseability — rubric §3.5 table + italic note**
1. Does the response parse on first attempt, with no wrapper prose or fences? → 3.
2. Does it fail to parse — including because it is wrapped in markdown fences or prose, even around an otherwise-perfect object? → **0**.
3. **Parseability is scored before the other three dimensions.** If parseability is 0, do not score schema conformance, enum/constraint conformance, or content correctness — mark all three `n/a` per §3.6 rule 1, so the failure attributes to format, not content, and is not double-counted.

**5.2 Schema conformance** *(only reached if parseability ≠ 0)*
1. Are all required keys present, with correct types, and no extra keys? → 3.
2. Does it violate the schema? → 0.

**5.3 Enum/constraint conformance** *(only reached if parseability ≠ 0)*
1. Are constrained/enum values respected? → 3.
2. Are values outside the permitted set? → 0.

**5.4 Content correctness** *(only reached if parseability ≠ 0)*
1. Are the values factually right? → 3.
2. Are the values wrong? → 0.

---

## 6. Case-level and task-level aggregation — rubric §3.6

1. **`n/a` is excluded from the denominator, not scored zero.** A case with two applicable dimensions scoring 3 and 2 scores the same as a three-dimension case scoring 3, 2, and their mean.
2. **Case score** = mean of applicable (non-`n/a`) dimensions → normalised to 0–100.
3. **Task score** = unweighted mean of the 20 case scores — not a mean of dimension means.
4. All 20 cases count toward the task score, adversarial included; the three adversarial cases are *additionally* reported as their own sub-score, not double-counted.
5. Every published task score carries its `n/a` count.

---

## 7. Median-of-three — rubric §3.7

1. **The median is taken per dimension**, across the three runs — not per case. Median feeds the §3.6 chain: median per dimension → case score → task score.
2. `n/a` never participates in a median. If **two or more of the three runs are `n/a`** for a dimension, that dimension is `n/a` for the case. Otherwise take the median of the numeric runs only, and record how many runs contributed.
3. Record the min–max spread across the three runs alongside every published median.

---

## 8. Open boundaries — explicitly unresolved, do not pick a side

**8.1 Precision / Normalisation boundary (extraction).** The precision anchor (§2.1) says a canonical-form-only defect belongs to normalisation and "must not be charged twice." It does not fully specify, for a field carrying both extra content and a canonical-form deviation, which dimension owns which part of the defect. This checklist states the anchor's rule (§2.1 rule 4 / §2.3 rule 3) and stops there. **Open**, per rubric — not resolved by this document.

**8.2 Recall / Normalisation / Null-handling boundary (extraction) — new.** Where a field is present and determinable in the source but the response returns `null` for it instead of extracting it: null handling (§2.4 rule 2) clearly scores this **1** (over-abstention). Whether the *same* miss should also reduce recall (§2.2), or whether a related formatting complaint on an adjacent field belongs to normalisation rather than recall, is not addressed anywhere in rubric §3.2. **Open** — this checklist does not assign recall a rule for this scenario.

**8.3 Conditional answerability (RAG Q&A) — new, disputed on adjudication.** `judge_prompt.md` v1.2's abstention rule (§4.3 above) branches binary on UNANSWERABLE/ANSWERABLE, decided from the gold answer alone. It has no representation for a question the context answers only *conditionally* — rag-t10's gold answer is "only if the purchase was a hardware bundle, which has a sixty-day window... any other purchase is outside the standard thirty-day window," not a flat yes or no. A response that lands on the majority-case answer ("No") without engaging the condition scores 3 under the binary branch as written, since it gave an answer on an ANSWERABLE case. This was put to the human scorer in `04-analysis/calibration/divergence_adjudication.md` (item 3): he disputes the binary reading, on the ground that landing on the majority case does not demonstrate the model resolved which branch of the condition applies, and held his own score (2) against both the checklist and the matching judge score (3). **Open** — this checklist does not assign abstention_calibration a rule for a conditionally-answerable case. Unlike §8.1 and §8.2, this boundary sits in a rule the judge was given (`judge_prompt.md` v1.2) that the rubric never carried at all — not a gap in an existing rubric anchor, but a scenario the operative rule itself never anticipated.

---

## 9. Operative rules never entered into the rubric — consolidated, NOT rubric content

**Method.** Every `conventions` block in all five case files (`summarization.json`, `extraction.json`, `classification.json`, `rag-qa.json`, `json-output.json`) was compared against every per-task `{{ANCHORS}}` and `{{DIMENSIONS}}` block in `judge_prompt.md` v1.3, and both against rubric §3's tables and italic anchors, in both directions. `summarization.json` carries no `conventions` block and nothing beyond what §1 above already restates from the rubric — no entry below. Test-design facts that don't change how a dimension is scored (e.g. "five label sets are used so a model can't memorise one taxonomy," "every instruction is self-contained") are excluded; only rules that govern a *score* are listed.

### 9.1 Classification (rubric §3.3 has no anchor covering any of this)

- **Label location.** The label is the first line of the response, and only the first line. `label_correctness` and `label_validity` are checked against that line alone. **Source:** `classification.json` `conventions.output_format`; `judge_prompt.md` v1.2 classification ANCHOR.
- **The `Note:` line.** An optional second line beginning `Note:` is the sanctioned channel for uncertainty. It is never itself the label, must not be read as an alternate answer, and its content must not be checked against the permitted label set. **Source:** `classification.json` `conventions.output_format` + `conventions.why_the_note_line`; `judge_prompt.md` v1.2 classification ANCHOR.
- **Unwarranted hedging costs a point.** Using the `Note:` line where no genuine ambiguity exists costs a point on `ambiguity_handling`. Rubric §3.3's table gives only the 3 and 0 poles for this dimension; this specific deduction is not in it. **Source:** `judge_prompt.md` v1.2 classification ANCHOR.
- **"However reasonable the reading."** A label outside the permitted set scores 0 on `label_validity` regardless of how defensible the reading is — this qualifier is not in the rubric table's "Invents a label outside the set" cell. **Source:** `classification.json` `conventions.no_new_labels`; `judge_prompt.md` classification ANCHOR.

### 9.2 RAG Q&A (rubric §3.4's table and anchors describe the behaviour generically; none of the following literal mechanics are in it)

- **Dimension rename.** Rubric §3.4 and both `human_scores*.json` files name this dimension `abstention`. `judge_prompt.md` v1.2 renamed it `abstention_calibration` (with the two-branch rewrite below) and every judge score file uses the new name. The rename was never carried back into the rubric. **Source:** `judge_prompt.md` v1.2 changelog entry.
- **Two-branch procedure.** Decide which branch a case is in — UNANSWERABLE or ANSWERABLE — from the **gold answer alone**, before scoring. Score only the branch that applies; answering an ANSWERABLE question correctly is never a deduction. **Source:** `judge_prompt.md` v1.2 §C `{{DIMENSIONS}}` block for `abstention_calibration`, and its ANCHOR.
- **Sanctioned token.** The literal string `INSUFFICIENT CONTEXT` is the abstention signal; nothing else is recognised as abstaining. **Source:** `rag-qa.json` `conventions.output_format` / `conventions.why_the_abstention_channel`; `judge_prompt.md` RAG ANCHOR.
- **Citation line format.** Citations appear on a final line of the form `Citations: P1, P3`, or `Citations: none` when abstaining. **Source:** `rag-qa.json` `conventions.output_format`; `judge_prompt.md` RAG ANCHOR.
- **Empty `supported_by` list.** Where the case's `gold.supported_by` is empty, no answer should have been given, and citing any passage is a citation-accuracy failure regardless of what it says. **Source:** `rag-qa.json` `conventions.citation_scoring`; `judge_prompt.md` RAG ANCHOR.

### 9.3 Structured JSON output (rubric §3.5's table already covers fencing — see checklist §5.1; the following two are not in it)

- **Key order is never scored.** JSON objects are unordered; scoring order would measure a serialisation incidental, not correctness. **Source:** `json-output.json` `conventions.key_ordering`. Not in `judge_prompt.md`'s ANCHOR either — this rule reached only the case file.
- **Null vs. omitted key.** Where a key is declared nullable, it must be present with a JSON `null` value; omitting the key entirely is a **schema conformance** failure, not a null-handling matter (json-output has no null-handling dimension). **Source:** `json-output.json` `conventions.null_vs_omit`. Not in `judge_prompt.md`'s ANCHOR either — this rule reached only the case file.

### 9.4 Extraction — found in the sweep, flagged, deliberately left out of the v1.8 draft

- **Canonical-form definitions.** Rubric §3.2's `normalisation` row says only "requested canonical form," without stating what that form is. The actual definitions — ISO 8601 `YYYY-MM-DD` dates, plain numbers with no symbol or thousands separator, ISO 4217 three-letter currency codes, `null` (never a guess or empty string) for absent fields — exist only in `extraction.json` `conventions` (`dates`, `amounts`, `currency`, `absent_fields`), restated per-instruction but never centralised in the rubric. **This is a genuine same-category gap.** It is listed here because the sweep was asked to be complete, but rubric v1.8 (per instruction) documents only §3.3, §3.4 and §3.5 — this one is left for the hub to decide whether a future amendment should cover it.

### 9.5 Direction swept in reverse: rubric §3 content absent from case files and judge_prompt.md

**None found.** Every italicised anchor in rubric §3 (§3.1 coverage, §3.2 precision and null-handling, §3.3 correctness/validity separation, §3.4 own-dimension and mirror-failure, §3.5 parseability-before-content) is carried into `judge_prompt.md`'s per-task `{{ANCHORS}}` block — three of them explicitly marked "verbatim" in the prompt file itself. The gap runs one way: outward from the operational materials into a rubric that was frozen before this run's edge cases were discovered.

---

*§§0–8 are sourced entirely from Scoring-Rubric.md v1.7 §2–§3.7; a rule not traceable to a table cell or an italicised anchor paragraph there does not belong in §§0–8. §9 is sourced entirely from case-file `conventions` blocks and `judge_prompt.md` v1.3's per-task substitutions, is explicitly not rubric content, and is marked as such at every entry.*

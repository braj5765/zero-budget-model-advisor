# Test Case Design — Zero-Budget Model Advisor

**v1.0 · 2026-08-10 · Owner: Braj**

100 cases: 20 per task, stratified 12 typical / 5 hard / 3 adversarial. Companion to the Scoring Rubric v1.0 §4.

---

## 1. Source material policy

**Every source text is original, written for this benchmark.**

This is the most important design decision here and the one most likely to be challenged, so the reasoning is explicit: if I used news articles, Wikipedia extracts, or well-known documents, models may have **memorised them during training**. A model reproducing a remembered summary would score well without having summarized anything — I'd be measuring recall and calling it comprehension. Contamination is the standard failure of hand-built benchmarks and it is invisible in the results.

Original sources also remove any copyright question from a project intended for public republication.

**Cost of this choice:** original text is more artificial than real-world input, and my writing has stylistic tics a model may find easier or harder than genuine documents. Stated in Known Limitations rather than hidden. The mitigation is deliberate variety of register — support tickets, meeting notes, product specs, invoices, policy text, chat logs — so no single voice dominates.

**Rotation:** each quarterly refresh replaces ~25% of cases, protecting against optimisation-against-the-set once the index is public (Decision Log C4).

---

## 2. Case schema

Every case, every task, is one JSON object:

```json
{
  "case_id": "sum-t01",
  "task": "summarization",
  "difficulty": "typical",
  "probes": "what failure this case is designed to induce",
  "source": "the input text",
  "instruction": "the task instruction given verbatim to every model",
  "gold": {
    "must_include": ["key point 1", "key point 2"],
    "must_not_include": ["claim absent from source"],
    "reference": "a model answer, for the judge to compare against",
    "notes": "scoring guidance for ambiguous dimensions"
  }
}
```

**Why `gold` is criteria-plus-reference rather than a single right answer:** for generative tasks there is no unique correct output. A judge comparing against one reference punishes valid alternative phrasings. `must_include` / `must_not_include` capture what actually determines correctness; `reference` gives the judge a calibration anchor for quality level. For extraction, classification and JSON, `gold` becomes an exact expected object — those tasks *do* have single right answers.

**Gold shape varies by task, and that is by design.** Summarization and RAG Q&A use criteria-plus-reference; extraction, classification and JSON use `gold.expected` as a literal object or label. Each case file declares its shape in a file-level `gold_form` key. **This branching belongs to `/scoring`, not `/harness`** — the harness never reads gold at all, it only records raw responses (Harness-Spec §1). Any gold-awareness appearing in the harness is a layering violation under CLAUDE.md.

**Citation ground truth.** RAG Q&A adds `gold.supported_by` — the passage IDs that actually support the answer, and the ground truth for the citation-accuracy dimension. Passage IDs are **case-local** (`P1`, `P2`…), not global. On correctly-unanswerable cases it is the **empty list**, which is a meaningful value and not a missing one: no passage supports an answer that shouldn't be given. `/scoring` must treat `[]` and absent as different — citing anything against `[]` is a citation failure.

**Multiple accepted answers.** Where a case is genuinely on a boundary and more than one answer is defensible, `gold.expected` is `null` and `gold.expected_any` holds the list of accepted answers. Declared **per case, never file-wide** — a file-wide accepted-set would soften every case in the file. `/scoring` must handle both shapes: `expected` present → exact match; `expected` null → membership test against `expected_any`. Introduced in `cls-a01` and `cls-a02`.

**Uncertainty needs a sanctioned channel.** Any dimension scoring calibration — ambiguity handling, abstention — is unmeasurable unless the output format gives the model a way to express doubt. A well-calibrated model and a falsely confident one otherwise emit identical output. Where a case file introduces such a channel (classification's optional `Note:` line), it must be offered on **every case in the file, not only the ambiguous ones** — otherwise the instruction itself signals which cases are traps and the model is rewarded for reading the prompt rather than the input. Using the channel where no ambiguity exists must carry a scoring cost, or it becomes free insurance.

**The `_raw` escape hatch.** Where a value is stated but cannot be normalised unambiguously from the source alone, the convention is: return `null` for the field and add a sibling key with the same name plus `_raw` holding the verbatim source text. This preserves the distinction between *absent* and *present but unresolvable* — collapsing those two into a bare null loses the information that the model saw the field at all. **Any case using this must declare it in its own `instruction`, and must not say "exactly these keys" elsewhere in that instruction.** Introduced in `ext-a02`; reuse this exact convention if another task needs it rather than inventing a variant.

**`must_not_include` is the hallucination trap.** Several cases contain plausible-sounding claims a model is likely to invent — a named cause, a rounded total, an implied conclusion — listed explicitly so the judge catches the fabrication instead of rewarding the fluency.

---

## 3. Stratification, per task

| Tier | n | Purpose |
| :---- | :---- | :---- |
| **Typical** | 12 | Ordinary builder workloads. Establishes the baseline. |
| **Hard** | 5 | Long inputs, noise, contradictions, unusual formats, mixed registers. |
| **Adversarial** | 3 | Engineered to induce this task's characteristic failure. Reported as its own sub-score. |

The adversarial three per task are where free tiers actually separate. Their design per task:

- **Summarization** — sources containing a plausible-but-unsupported inference, contradictory statements, and a buried lede that a naive summary will miss.
- **Extraction** — fields genuinely absent (tests null handling vs fabrication), fields present in a misleading format, and a near-duplicate field pair.
- **Classification** — inputs sitting on a category boundary, an input belonging to no permitted label, and one with sentiment-vs-content mismatch.
- **RAG Q&A** — a question the context cannot answer (tests abstention), a question whose answer is contradicted between two passages, and a question whose plausible answer appears in an irrelevant passage.
- **JSON** — deep nesting, a constrained enum plus an optional null field, and an instruction likely to trigger explanatory prose around the JSON.

---

## 4. Fixed conditions

- Identical instruction text to every model. No per-model tuning (Decision Log B4).
- Temperature 0 where supported; three runs; median score.
- Sources kept under ~400 words so context limits never confound the comparison — with one hard case per task deliberately longer, to measure exactly that.

---

## 5. File layout

```
01-rubric-and-testcases/
  Scoring-Rubric.md            (living doc; version in header + changelog)
  Test-Case-Design.md
  cases/
    summarization.json
    extraction.json
    classification.json
    rag-qa.json
    json-output.json
```

Case files are **append-only and versioned**. A case is never edited after a run has used it; a flawed case is superseded by a new `case_id` and the original retained, so historical results stay interpretable.

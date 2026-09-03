# Judge Prompt — v1.3

**Authored 2026-08-20, BEFORE `sealed_model_map.json` was opened.** Nothing in this file could have been shaped by knowing which model produced which response. That ordering is the point; it is why this was written first.

Scores against **Scoring-Rubric.md v1.4**. Judge model and version are recorded per index release (§5).

**Assembly:** `{{SCALE}}`, `{{NA_RULE}}` and `{{OUTPUT}}` are constant. `{{DIMENSIONS}}` and `{{ANCHORS}}` are substituted per task from §B. `{{...}}` case fields come from the case file and the raw run record. One call per (case, model) response.

---

## A · Prompt template

```
You are scoring one model response against a fixed rubric. You are not the author of the
response and you do not know which model produced it. Score only what is in front of you.

SCALE
{{SCALE}}

DIMENSIONS FOR THIS TASK
{{DIMENSIONS}}

{{ANCHORS}}

NOT-APPLICABLE RULE
{{NA_RULE}}

WHAT YOU ARE SCORING
Task: {{TASK}}
Instruction given to the model:
{{INSTRUCTION}}

Source material provided to the model:
{{SOURCE}}

Gold reference / expected answer:
{{GOLD}}

What this case was designed to probe:
{{PROBES}}

Scoring notes for this case (authoritative where they conflict with your own reading):
{{GOLD_NOTES}}

Model response — RAW AND UNMODIFIED. Markdown fences, prose wrappers, leading or trailing
text are part of the response and must be scored as such. Do not mentally clean it up.
<<<RESPONSE
{{RESPONSE_TEXT}}
RESPONSE>>>

RULES
1. Score every dimension listed above, in the order listed.
2. Use only 0, 1, 2, 3 — or "n/a" where and only where the scoring notes above say the
   dimension is unscoreable for this case. You may never decide a dimension is n/a
   yourself.
3. Give exactly one sentence of justification per dimension, naming the specific thing in
   the response that decided the score. "Good summary" is not a justification.
4. Judge the response as delivered, not the response you would have written.
5. Do not reward or penalise length, tone, or confidence except where a dimension says to.

{{OUTPUT}}
```

---

## B · Constant blocks

### `{{SCALE}}` — rubric §2, verbatim

```
Every dimension is scored 0-3. Four points, no midpoint.
3 - Fully correct. A competent practitioner would ship this unchanged.
2 - Correct in substance, minor flaw. Usable after a trivial edit.
1 - Materially flawed. Contains an error a user would have to catch and fix.
0 - Unusable or wrong in a way that would mislead the user.
```

### `{{NA_RULE}}` — rubric §3.6 rule 1, verbatim

```
A dimension may be marked n/a only where the case design makes it unscoreable, and the
case's scoring notes must say which dimensions are n/a and why. A judge may never mark
n/a at its own discretion.
```

### `{{OUTPUT}}`

```
OUTPUT
Return a JSON object and nothing else:
{"scores": {"<dimension>": <0|1|2|3|"n/a">, ...},
 "justifications": {"<dimension>": "<one sentence>", ...}}
Use the exact dimension names given above, lowercased, spaces as underscores.
```

*Note for `/scoring`: the judge's **own** output may be fence-wrapped and may be stripped before parsing. That is not a contradiction of §4b.2 — the no-cleaning rule protects the **model response being scored**, which is the measured artifact. The judge's reply is instrumentation, not data.*

---

## C · Per-task substitutions

### Summarization

`{{DIMENSIONS}}`

```
faithfulness  - 3: every claim traceable to the source; nothing invented.
                0: contains a claim contradicted by or absent from the source.
coverage      - 3: captures all key points identified in the gold reference.
                0: misses the primary point of the source.
concision     - 3: within the requested length; no padding or restatement.
                0: substantially over length, or mostly filler.
instruction_adherence - 3: honours format, length, tone and audience as instructed.
                0: ignores the instruction.
```

`{{ANCHORS}}` — **rubric v1.4 §3.1, verbatim. Carried because the human scorer applied it; an anchor the judge cannot see manufactures disagreement that reads as judge error.**

```
COVERAGE ANCHOR
Coverage is judged by significance and against the length the instruction permits - never
by counting gold points. If the point the case was designed to probe (its probes field, or
the point named in gold.notes) is missed, coverage caps at 1 however many other points
landed. If the probed point lands, coverage is 3 where the omitted points are ones the
requested length could not accommodate, and 2 where the summary had room and still dropped
a substantive point. The length clause is load-bearing: a three-sentence summary cannot
carry five gold points, and marking it down for obeying the length instruction
double-counts the same behaviour against instruction adherence, which is its own dimension.
```

### Extraction

`{{DIMENSIONS}}`

```
precision     - 3: no extracted field is wrong or hallucinated.
                0: majority of fields wrong or fabricated.
recall        - 3: all fields present in the source were extracted.
                0: most present fields missed.
normalisation - 3: dates, numbers, units, names in the requested canonical form.
                0: raw or inconsistent forms throughout.
null_handling - 3: absent fields returned as null, AND determinable fields resolved
                   rather than nulled.
                0: fabricates plausible values for absent fields, or nulls fields the
                   source does determine.
```

`{{ANCHORS}}` — **rubric v1.4 §3.2, verbatim**

```
PRECISION ANCHOR
Precision scores whether the value is correct, not how it is worded. A semantically
equivalent rewording of the correct value scores 3. A value carrying content the gold does
not contain scores 2 - the field is not the requested value and a consumer must edit it -
or lower where that content is not in the source at all, which is fabrication. Differences
of canonical form (date format, unit, casing, separators) are normalisation's business,
not precision's, and must not be charged twice.

NULL HANDLING ANCHOR
Over-abstention is scored here too, and symmetrically. Fabrication scores 0; nulling a
determinable value scores 1. Inventing a value misleads silently, while over-nulling
merely under-delivers.
```

### Classification

`{{DIMENSIONS}}`

```
label_correctness  - 3: matches the gold label.  0: wrong label.
label_validity     - 3: output is a member of the permitted label set.
                     0: invents a label outside the set.
ambiguity_handling - 3: on deliberately ambiguous cases, flags or picks the defensible
                        label.
                     0: picks confidently and wrongly with no signal of uncertainty.
```

`{{ANCHORS}}`

```
The classification label is the first line of the response, and only the first line.
Check label_correctness and label_validity against that line alone. Any second line
beginning "Note:" is a separate, optional channel for uncertainty (see ambiguity
handling below) — it is never itself the label, must not be read as an alternate
answer, and its content must not be checked against the permitted label set.

The permitted label set is stated in the instruction. Any string outside it is a
label-validity failure scored 0 however reasonable the reading - this is the
integration-breaking failure the rubric separates from correctness. The optional
"Note:" line is the sanctioned channel for uncertainty; using it where no genuine
ambiguity exists costs a point on ambiguity handling.
```

### RAG Q&A

`{{DIMENSIONS}}`

```
groundedness      - 3: every assertion supported by the supplied context.
                    0: asserts facts not in the context.
answer_correctness- 3: factually answers the question asked.  0: wrong answer.
abstention_calibration - First decide which branch this case is in, from the gold
                       answer alone: UNANSWERABLE (gold answer is INSUFFICIENT
                       CONTEXT) or ANSWERABLE (gold gives a real answer).
                       If UNANSWERABLE: 3 if the response states INSUFFICIENT
                       CONTEXT, 0 if it answers anyway.
                       If ANSWERABLE: 3 if the response gives the answer, 0 if it
                       states INSUFFICIENT CONTEXT instead of answering.
                       Score only the branch that applies to this case. Answering
                       an ANSWERABLE question correctly is the 3 case, never a
                       deduction — do not score this dimension by checking whether
                       the response used the INSUFFICIENT CONTEXT token in
                       isolation from whether this case needed it.
citation_accuracy - 3: points to the passage that actually supports the claim.
                    0: cites a passage that does not support it.
```

`{{ANCHORS}}`

```
Abstention is symmetric. A model that abstains on answerable questions is not being
careful; it would otherwise game this dimension by refusing everything. Check the gold
answer's branch (§C dimensions block above) before scoring abstention_calibration —
never penalise a response for answering when the gold answer itself is not
INSUFFICIENT CONTEXT. The sanctioned abstention token is INSUFFICIENT CONTEXT, and
citations appear on a final "Citations:" line. Where the supporting-passage list is
empty, no answer should have been given and citing anything is a citation failure.
```

### Structured JSON output

`{{DIMENSIONS}}`

```
parseability   - 3: parses on first attempt, no wrapper prose or fences.
                 0: fails to parse.
schema_conformance - 3: all required keys present, types correct, no extra keys.
                 0: violates the schema.
enum_constraint_conformance - 3: constrained/enum values respected.
                 0: values outside the permitted set.
content_correctness - 3: values are factually right.  0: values wrong.
```

`{{ANCHORS}}`

```
Parseability is scored before content. Markdown fences around an otherwise perfect object
are a parseability failure, not a formatting quibble - the response as delivered does not
parse. If the response is unparseable, score parseability 0 and mark the content
dimensions n/a per the not-applicable rule, so the failure is attributed to the right
dimension rather than double-counted.
```

---

## D · Blinding and order (§5)

- **Model identity is never in the prompt.** No provider name, model tag, or anything from `sealed_model_map.json` appears in any substitution. Items are addressed by `item_id` only.
- **Presentation order is randomised** with a recorded seed, so position cannot correlate with model. On the 20-item calibration set each item is judged independently in a fresh context — nothing carries between calls, which removes order effects rather than merely shuffling them.
- **Judge model and version are pinned and recorded** per index release. A judge version change invalidates cross-release comparison and forces a re-run.
- **Judge sits outside the benchmark set.** `qwen2.5` is unrelated to Gemini, Groq's Llama, Mistral, and the benchmarked `llama3.2:3b`.

---

## Changelog

| Version | Date | Change |
| :---- | :---- | :---- |
| 1.3 | 2026-08-28 | **Added `{{PROBES}}` to §A, populated from the case's `probes` field, placed immediately before `{{GOLD_NOTES}}` under the label "What this case was designed to probe:". No other change** — no anchor added or reworded, no dimension table touched. **Reason:** rubric v1.4 §3.1's coverage anchor instructs the judge to consult the case's `probes` field or `gold.notes` to identify "the point the case was designed to probe," but the template only ever assembled `gold.notes` — the anchor named an input the prompt never supplied. This supplies a required input; it does not change what's being measured. Motivated by cal-14 (`sum-a01`), which missed the coverage cap on *both* the 7B judge (v1.2, `disagreement_audit.md` #9) and the materially stronger hosted judge (v1.2, `disagreement_audit_hosted.md` #3) — the same miss on two different judges is the signal that the gap is in what the judge was shown, not in either judge's capability. **Falsification test, recorded before the re-judge so it can't be shaped by the result:** adding `probes` cannot move any human score, because the human scorer already had the case file — including `probes` — in front of them when scoring blind (`human_scores.json`, 2026-08-20). If this run's κ moves, the movement is confined to closing a judge/human information gap, not to a standard that shifted. |
| 1.2 | 2026-08-28 | **Two mechanical-misreading fixes, both from the v1.0 20-item calibration audit (`04-analysis/calibration/disagreement_audit.md`).** (1) RAG Q&A dimension renamed `abstention` → **`abstention_calibration`** and rewritten as an explicit two-branch check (decide UNANSWERABLE vs ANSWERABLE from the gold answer first, then apply that branch's rule) — motivated by cal-02, cal-03, cal-07 and cal-13, all four ≥2-point disagreements on this dimension in the 20-item set, all with the judge scoring 0 for "confidently answers without abstaining" on responses that correctly answered an answerable question. The anchor now explicitly says never to penalise answering an ANSWERABLE question. (2) Classification anchor now states the label is the first line of the response only, and that a second "Note:" line is never the label and is not checked against the permitted set — motivated by cal-01, where the judge scored `label_validity: 0` on the claim that "Cancel Subscription" (the actual, and only, first-line label) was outside the permitted set, despite it being the first label named in the instruction; the response's second line happened to contain the correct label text, and the fix removes the ambiguity about which line is being scored. **Deliberately not addressed this pass** (out of scope, per the audit): cal-03's citation-error bleed into `groundedness`/`answer_correctness` (no anchor separates citation defects from assertion-content dimensions), and cal-14's coverage miss (the case-level `probes` field is never assembled into the judge's prompt by `judge.py`, only `gold.notes` is — an implementation gap, not a wording gap). Both remain open for a future prompt or `judge.py` change. |
| 1.1 | 2026-08-20 | Renamed json-output dimension `constraint_conformance` → **`enum_constraint_conformance`**, matching rubric §3.5 and `human_scores.json`. v1.0 deviated from both. The in-flight calibration run used v1.0 names; `agreement.py` maps that one name explicitly, with this changelog entry as the reason — the mapping is documented, not silent, and is removed once a run under v1.1 exists. |
| 1.0 | 2026-08-20 | Initial. Authored pre-unsealing, against rubric v1.4. |

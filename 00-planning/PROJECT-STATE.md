# PROJECT STATE — Zero-Budget Model Advisor

> **Read this first.** If you are a fresh chat, agent, or future me picking this project back up, this file is the entry point. It is the single source of truth for where the project stands. Everything else is detail hanging off it.
>
> **Last updated: 2026-08-11 · Phase: 2 of 6 (Harness build) · Status: on track**

---

## 1. What this project is, in four lines

An original benchmark of **free-tier LLMs** across five everyday builder tasks, plus a routing advisor built on the results, published as a quarterly-refreshed public index.

Built by Braj as an AI PM portfolio project. The zero-budget constraint is the thesis, not a limitation: nobody has rigorously published what you can actually ship on a free tier. Target: **2 weeks from 2026-08-10.**

The interview goal is to demonstrate — not claim — eval design, hallucination handling, fallback design, and explicit cost/latency/quality tradeoffs.

---

## 2. Where things stand

| Phase | Status | Output |
| :---- | :---- | :---- |
| 0 · Planning | **Done** | PRD, Decision Log, UX & Feedback Spec, CLAUDE.md |
| 1 · Rubric & test cases | **Done** | Rubric **v1.2** ✅ · Design doc ✅ · **All 5 case files — 100 cases, 12/5/3 stratification verified in each** |
| 2 · Harness | Spec done, not built | Harness-Spec.md ✅ · code not started |
| 3 · Run benchmark | Not started | ~1,500 calls → `/03-results` |
| 4 · Analysis | **Ready to start** | Scoring, κ check, breakeven model, selection memo. Blocked on open question 1 (judge model). |
| 5 · Site + advisor | Not started | Static site, client-side advisor, feedback widget |

### Immediate next action

**Phase 3 done.** The benchmark ran 2026-08-15 → 2026-08-16 (24.8h wall clock). 1,500 rows, 0 duplicate `(case_id, model_id, run_index)`, 0 rows missing token counts, no silent model-version swaps. Three `git_commit` values across the file, all legible (12 rows `-dirty` from before the Phase 2 commit; 22 rows after the `_estimate` fix).

**Next: Phase 4.** Blocking item is **open question 1 — the judge model**, still unresolved. Two things `/scoring` must handle, both now load-bearing:

1. **Score four models, not five.** OpenRouter is cut (§4). Its 204 `RATE_LIMIT` rows stay in `/03-results` as evidence and feed the failure-rate table; they are excluded from quality scoring.
2. **Audit before publishing failure codes.** Every `RATE_LIMIT` row's `error_raw` must be read and reclassified from observed provider strings — the harness matched `"quota"` loosely on purpose, deferring classification to where the evidence exists.

Also for `/scoring`: the failure taxonomy is **split by design** — five transport codes in `02-harness/clients/base.py`, three content codes in `04-analysis/scoring/failure_codes.py`; `Scoring-Rubric.md` §6 stays canonical for all eight. Three gold shapes exist across the case files — criteria-plus-reference (summarization, rag-qa), literal expected object (extraction, json-output, incl. one top-level array), and label with optional `expected_any` (classification) — plus the `_raw` and `INSUFFICIENT CONTEXT` conventions. See §8 for per-file notes.

---

## 3. File map

```
Zero-Budget-Model-Advisor/
  00-planning/
    PROJECT-STATE.md              ← you are here
    PRD-Zero-Budget-Model-Advisor-2026-08-10.md
    Product-Decision-Log-...md    ← 16 decisions + how to defend each
    UX-and-Feedback-Spec-...md
    CLAUDE.md                     ← move to repo root at git init
  01-rubric-and-testcases/
    Scoring-Rubric.md             ← living doc, currently v1.2. Version in header + changelog.
                                     Pre-run amendment is allowed and logged; post-run change
                                     requires re-scoring, not patching.
    Test-Case-Design.md
    cases/*.json                  ← 5 files, 100 cases total
  02-harness/  Harness-Spec.md
               SETUP-AND-TROUBLESHOOTING.md  ← context file for the environment/tooling spoke
  03-results/  (empty — append-only when populated)
  04-analysis/ (empty)
  05-site/     (empty)
```

---

## 4. Decisions that are closed — do not reopen without new information

Full reasoning and challenge-responses live in the **Product Decision Log**. Summary so a fresh chat doesn't relitigate:

**Scope:** Free tiers only, not frontier. Five tasks (summarization, extraction, classification, RAG Q&A, structured JSON). **Four providers: Gemini, Groq, Mistral, Ollama local.** **No overall leaderboard** — it would contradict the product's thesis.

**OpenRouter cut 2026-08-16 — reopened and closed on new information, per §4's own standard.** The benchmark run returned **96 successes out of 300 attempts (68% `RATE_LIMIT`)** across 19.4 hours, against documented limits of 20 rpm / 50 rpd. 96 successes cannot support median-of-three over 100 cases, and the 12/5/3 stratification breaks at that coverage. Per §7, models are cut before the calibration set. **The exclusion and its reason are published, not hidden.** Retained for publication: the failure rate, the daily-cap behaviour, and the O-1 finding that `:free` models are callable at a zero credit balance despite the terms.

**Correction (2026-08-16, same day):** an earlier version of this entry claimed the documented 50/day cap was "contradicted in both directions", citing 241 calls served on 15 Aug. That was wrong — 241 was the number of *attempts*, of which 194 were rejected. Successes per calendar day were **47 (15 Aug) and 49 (16 Aug)**, which matches the documented 50/day almost exactly, and OpenRouter's own 429 body confirms it (`X-RateLimit-Limit: 50`, `limit_source: openrouter_free_tier_daily`). **OpenRouter's documented limit is accurate.** The real finding is narrower and still worth publishing: a documented 50/day makes a 300-call benchmark take six days, which is what forced the cut — not any discrepancy in the provider's own numbers. Not retained: any quality score. The 204 `RATE_LIMIT` rows stay in `/03-results` as evidence; `/03-results` is append-only and nothing was deleted.

**Rejected and settled:** agentic/tool-use suite (free tiers fail outright), multilingual suite (audience too narrow), reasoning/coding benchmarks (commoditised), standalone eval workbench product (crowded market).

**Method:** Rubric frozen before any run. 0–3 scale, no midpoint, unweighted dimensions (the *advisor* handles weighting at query time). LLM-as-judge over all cases, calibrated against 20 hand-scored cases, gated at **quadratic-weighted Cohen's κ ≥ 0.6**. Judge sits **outside** the benchmark set, blinded, order-randomised. Identical untuned prompts across all models. Temp 0, three runs, median. Refusals and errors excluded from quality and reported as failure rates.

**Product:** Static site, client-side advisor over a JSON data file, no backend, no accounts. Quarterly refresh. In-page feedback widget → Google Form. Everything published — rubric, cases, gold answers, judge justifications.

**Test cases:** All source text is **original, authored for this benchmark** — public text risks training-data contamination, which would measure recall rather than comprehension. Gold shape varies by task and is declared per file in `gold_form`; **that branching lives in `/scoring`, never in `/harness`**, which does not read gold at all. Over-abstention is an explicit failure (rubric v1.1) — test sets must pair "correctly refuse" cases with superficially similar answerable ones.

---

## 5. Open questions

| # | Question | Blocks | Owner |
| :---- | :---- | :---- | :---- |
| ~~1~~ | **CLOSED 2026-08-17 — the judge is a local Ollama model outside all four benchmarked families: `qwen2.5:7b`, or `14b` if RAM allows.** The deciding constraint was **re-runnability, not quality**: rubric §5 requires sharpening anchors and re-judging the *whole set* if κ < 0.6, and ~400 responses × 3–4 dimensions with written justifications is a multi-day cycle on a hosted free tier with a 1,000/day cap — a second pass another multi-day cycle. A κ gate that is expensive to enforce is a κ gate you are tempted not to enforce, which defeats it. Local is unlimited and an overnight re-judge is free. Three supporting reasons: judging is the one workload where **latency is irrelevant** (the judge is not being benchmarked); §5 requires the judge model *and version* be pinned per index release, and a local tag is pinned by definition whereas a hosted free tier can swap versions silently; and today's OpenRouter shared-pool finding disqualifies that route outright — a judge that rate-limits unpredictably mid-scoring yields a partial pass that cannot be cleanly resumed. Qwen is unrelated to Gemini, Groq's Llama, Mistral and the benchmarked Llama-3.2-3b, so **Decision B3's self-preference concern is clean**, and a 7B judging a 3B is the correct direction (judge stronger than judged). **Validation sequence, fixed:** (1) hand-score the 20 calibration cases blind from the rubric alone — a prerequisite either way; (2) judge only those 20 with the candidate; (3) compute κ; (4) κ ≥ 0.6 → proceed to the full set, κ < 0.6 → sharpen anchors, re-judge the 20, retry — free, so iterate; (5) still failing after two attempts → **hand-score a reduced set with real scores rather than ship an uncalibrated judge**, the ordering already fixed in §7. **Try 14b before concluding a local judge cannot clear the bar** — the 7b→14b jump on judgment tasks is usually larger than the parameter count suggests. | — | done |
| ~~2~~ | **CLOSED 2026-08-13** — all four reviewed, see `ToS-Review.md`. No provider bars benchmarking or publication. Three consequences: Groq is **never actively probed** (AUP), Gemini trains on free-tier input so case rotation ≥25% per refresh is now **required**, and "adversarial" cases must be publicly distinguished from Red Teaming. | — | done |
| ~~2b~~ | **CLOSED 2026-08-13** — OpenRouter `:free` model returns a completion on a zero balance despite terms stating credits are required. **Model set confirmed at five.** Gap published in its profile; re-verify each refresh. | — | done |
| ~~3~~ | **CLOSED 2026-08-13** — resolves itself on first real call per provider; harness records `tokens_estimated: true` where absent. | — | done |
| 4 | Hosting — GitHub Pages assumed but not confirmed. | Phase 5 | Braj |
| 5 | Is a 2-week timeline realistic for ~1,500 rate-limited calls? | Phase 3 | Braj |

---

## 6. How to work on this project

**Hub & spoke.** One hub chat holds decisions and sequencing. Bulky, self-contained work goes to spoke chats — one per workstream (test cases, harness build, analysis, site), not one per context overflow.

**Rules:**

1. **Every spoke chat reads this file first.** It is the handoff mechanism. No verbal re-briefing.
2. **Nothing exists unless it's in a file.** A decision that lives only in a chat is lost at the next context boundary. New decisions go in the Decision Log; status changes go here.
3. **Update this file at the end of every session** — phase table, next action, open questions. A stale PROJECT-STATE is worse than none, because it will be trusted.
4. **Code work obeys `CLAUDE.md`.** Smallest correct change; abstract on the third occurrence, not the first; no unrequested error handling.

**Where each spoke runs:**

- **Content spokes** (test cases, memo, site copy) → a fresh Cowork chat.
- **Code spokes** (harness, scoring, analysis, site build) → **Claude Code in Cursor, at the repo root**, so `CLAUDE.md` loads automatically and the agent can run what it writes. Do not build code in a Cowork chat — an agent that cannot execute its own code will hand you plausible-looking untested files.

**Spoke prompt template — content work:**

> Read `PROJECT-STATE.md` and `Test-Case-Design.md` in the Zero-Budget-Model-Advisor folder, then read an existing file in `cases/` as the pattern to follow.
>
> [task-specific instruction]
>
> Do not change the rubric or reopen closed decisions. When done, append to PROJECT-STATE §8 and tell me what else needs updating.

---

## 7. Risks being actively managed

- **Timeline** — ~1,500 rate-limited calls across days is the binding constraint. **If it slips, cut models before cutting the human-scored calibration set.** A smaller model set is a scoping decision; an uncalibrated judge is a credibility hole.
- **Rubric defensibility** — mitigated by pre-freeze, published cases, published judge justifications, and an audited disagreement set.
- **Staleness** — mitigated by making refresh cadence part of the product, and by dating every published surface.
- **Scope creep** — the five tasks and five providers are fixed for v1. New task types are a v2 decision.
- **ToS exposure** — rate-limit probing is the legally sensitive part. Terms reviewed per provider first; one account each; no circumvention; a provider that prohibits publication is dropped and the exclusion disclosed.

---

## 8. Session log

| Date | Phase | What happened |
| :---- | :---- | :---- |
| 2026-08-17 | 3→4 | **Open question 1 closed — judge is local Qwen; Decision A5 (OpenRouter cut) written to the Decision Log including the attempts-vs-successes correction.** Full judge reasoning in §5. The correction was kept visible in A5 rather than tidied away: a decision log containing only conclusions its author still likes is not evidence of judgment. Remaining before Phase 4 scoring can start: hand-score the 20 calibration cases blind, then κ-test the candidate judge on those 20 only. Remaining before publication: the retrospective OpenRouter/Darkbloom terms check as a dated section in `ToS-Review.md`. |
| 2026-08-17 | 3 | **Rate-limit probing complete — measured ceilings for all three permitted providers.** Ollama and Groq skipped by config flag (`provenance: documented + incidental`); Gemini, Mistral and OpenRouter probed with backoff disabled, stopping at the first sustained limit. Results and what they mean: (1) **Gemini's documented 15 rpm is confirmed by the provider itself** — the 429 body states `limit: 15, model: gemini-3.5-flash-lite` outright, which is a better source than the docs page (which no longer prints free-tier figures) or the AI Studio console. Measured 16.6 rpm at first rejection, 39 requests in; `Please retry in 55.9s` confirms per-minute. Open question on Gemini's documented figures is **closed**; `config.toml` now cites the 429 body. Note the daily cap (`documented_rpd = 1000`) remains unverified — the probe stops at the first ceiling, which was the per-minute one. (2) **Mistral measured 52.1 rpm at rejection, 96 requests in**, against a documented 1 rps (60 rpm) — consistent. Its error prose is bare (`"Rate limit exceeded"`, code 1300) with no period word, so `limit_period_guess` is correctly `unknown` rather than guessed; classify at analysis time from the observed string. (3) **OpenRouter has two distinct ceilings, and the second one is a genuine finding.** During the benchmark its 429s carried `limit_source: openrouter_free_tier_daily` with `X-RateLimit-Limit: 50` — the account's daily cap. During the probe, with a fresh daily quota, it rejected after **2 requests** with `limit_source: upstream_provider_shared_pool`, `provider_name: Darkbloom`, `"temporarily rate-limited upstream"`. That is not the user's quota at all: it is contention in a pool shared across every OpenRouter free-tier user, and it is neither documented, predictable, nor controllable by the builder. **This explains the 68% benchmark failure rate better than the 50/day cap does**, and it is the strongest single argument in the OpenRouter model profile — a free tier whose availability depends on other people's traffic. Publish both ceilings, labelled by `limit_source`. **Two Phase 4 landmines, same pattern — the raw data contains provisional claims that must not be read at face value:** (a) `probe.jsonl` now holds **6 rows, only 3 of which have the `ceiling_reached` key**; the 3 older rows assert a ceiling at 200 requests that never happened (they predate the honest-recording fix). `/scoring` must take the **latest row per `model_id`** and treat a missing `ceiling_reached` as untrustworthy — `/03-results` is append-only, so the bad rows stay. (b) Every `RATE_LIMIT` row's `error_raw` in the benchmark file must be audited and reclassified from observed provider strings before the failure-rate table is published; the harness matched `"quota"` loosely on purpose. |
| 2026-08-16 | 3 | **Benchmark run complete — Phase 3 done, model set cut to four.** 1,500 rows in `run-2026-08-15T114622Z.jsonl` over 24.8h. Gemini, Groq, Mistral and Ollama each 300/300 successful. **OpenRouter: 96 successes, 204 `RATE_LIMIT`, cut from the index** (reasoning in §4). Findings to carry into Phase 4 and into publication: (1) **OpenRouter's documented 50/day is accurate, and it is the binding constraint** — successes per calendar day were 47 and 49 against a documented 50, with the provider's own 429 headers confirming `X-RateLimit-Limit: 50`. An earlier reading of this data claimed the documented figure was contradicted; that conflated attempts with successes and is corrected in §4. Attempts vs successes must be distinguished everywhere in the analysis — 300 attempts producing 96 successes is a *coverage* fact, not a rate-limit discrepancy. (2) **Groq produced an incidental ceiling observation** — 8 retries and one call that waited 1,075s in backoff on a `Retry-After` Groq itself sent. Since Groq may never be actively probed (ToS-Review R-1), this is the `documented + incidental` evidence that policy anticipated, and it is already in the raw records. (3) **Latency separates cleanly and honestly**, because backoff was kept out of `latency_ms`: median latency Groq 578ms · Mistral 1,078ms · Gemini 1,172ms · OpenRouter 10,678ms · Ollama 17,422ms (p95 68s, local 3B on CPU). OpenRouter's figure is its speed, not its rate-limiting — the `queue_wait_ms` separation earned its place. (4) **No silent model-version swaps** in any model over 1,500 calls; every `model_version` matched what was requested. Worth re-checking each quarterly refresh rather than assuming. (5) **Every provider returned native token counts** — open question 3 resolves empirically: zero rows needed estimation. The estimation path did fire once transiently on OpenRouter and crashed the run (a `NameError` left by the retry-policy refactor, fixed at row 1,478 with no data loss), which is also the proof that resumability works under a real unplanned crash, not just a simulated one. (6) **Design limitation now visible: resumability cannot retry failures.** §4 keys on the existence of a `(case_id, model_id, run_index)` row, so a `RATE_LIMIT` row is treated as done. This is correct — retrying failures is how a benchmark launders its own failure rate — but it means recovering rate-limited coverage requires a separate run file, not a resume. That trade is what made cutting OpenRouter the cheaper option. |
| 2026-08-11 | 1 | `cases/rag-qa.json` written — 20 cases, 12 typical / 5 hard / 3 adversarial, all passages original. 70 passages total, 3–5 per case, every case carrying at least one irrelevant or only-tangentially-relevant passage because that is what real retrieval returns. Three notes for the harness and scoring: (1) an explicit abstention channel — the exact token `INSUFFICIENT CONTEXT` plus a final `Citations:` line — is offered on **all 20 cases**, following the classification `Note:` precedent in Test-Case-Design §2: abstention (rubric §3.4) is unmeasurable without a sanctioned, parseable way to express it, and offering it only on the unanswerable cases would let the instruction signal which cases are traps. Scoring must parse the last line as citations and the body for the abstention token. (2) `gold` is criteria-plus-reference with two RAG-specific keys — `gold.supported_by` (passage IDs that actually support the answer; **empty list on the two abstention cases**, where the only correct citation line is `Citations: none`) is the ground truth for citation accuracy and is scored independently of whether the answer text was right. (3) Passage IDs are **local to each case** (P1, P2, …) and must never be compared across cases. Adversarial three: an unanswerable erasure-timeline question surrounded by plausible retention numbers that answer adjacent questions (rag-a01); a 99.9% vs 99.5% uptime figure contradicted between a pricing page and an MSA schedule with no stated precedence, where naming both and the absence of a precedence rule scores 3 and asserting that the contract supersedes the marketing copy is a groundedness failure because the passages never say so (rag-a02); a Documents-module file-size question whose only size figure belongs to a deprecated, separate-store Attachments widget, testing topic-similarity matching against actual relevance (rag-a03). Per rubric §3.4, rag-a01 is paired with **two** answerable cases in the same domain, register and question shape — rag-t05 (explicit, single passage) and rag-t11 (answerable only via a two-passage inference, so it is the case most likely to draw a false abstention); the adversarial sub-score must be read together with that pair, since a model scoring 3 on a01 and 0 on t05/t11 has learned caution, not judgment. Also note rag-h03, which splits the abstention dimension inside a single case — half the question is answerable and half genuinely is not, so blanket `INSUFFICIENT CONTEXT` scores 1, not 3 — and rag-h05, which is supersession (dated, stated) rather than contradiction, so hedging it like a02 is over-hedging. No rubric change needed: v1.2 §3.4 and §3.6 covered every case, including the empty-`supported_by` shape. |
| 2026-08-11 | 1 | `cases/classification.json` written — 20 cases, 12 typical / 5 hard / 3 adversarial, all sources original. Five label sets rotate across the file (sentiment, support routing, intent, priority, content category) so no model can succeed by memorising one taxonomy; every `instruction` states its complete permitted set inline and repeats the source verbatim, so each prompt is self-contained. Three notes for the harness and scoring: (1) a uniform output convention — label on line one, optional second line beginning `Note:` — is offered on **all 20 cases**, not just the ambiguous ones, because ambiguity handling (rubric §3.3) is unmeasurable without a sanctioned channel for uncertainty, and offering it selectively would let a model pass by reading the instruction rather than the input; scoring must therefore parse line one for correctness/validity and line two for ambiguity handling. (2) Two cases have no single gold label and use `gold.expected: null` plus `gold.expected_any: [...]` — the comparator must handle this shape; it is the classification analogue of extraction's `_raw` escape hatch. (3) cls-a02 scores only **two** of the three dimensions — label correctness is not-applicable and must be recorded as such, not as a miss, since no permitted label is right. Adversarial three: genuine Billing/Technical boundary where the bare-label answer scores 1 and naming the alternative scores 3 (cls-a01); a research enquiry against a four-label set with the `Other` escape deliberately removed, where returning "Other" is the failure (cls-a02); a polite, self-blaming report of eleven thousand deleted clinical records, gold P1, deliberately paired with typical case cls-t10 — a furious message about a wrong name in a PDF footer, gold P4 — so a tone-following model gets both wrong and the pair is read together in the adversarial sub-score. No rubric change needed: §3.3's three dimensions covered every case without amendment. |
| 2026-08-11 | 1 | `cases/json-output.json` written — 20 cases, 12 typical / 5 hard / 3 adversarial, all sources original. This file measures **format reliability, not content difficulty**: sources are deliberately short and unambiguous so failures attribute to structure, and schema complexity is the variable that moves (flat → mixed types → nested → arrays of scalars → arrays of objects → nullable → enums → top-level array). Every instruction carries the full schema inline. Adversarial three: deep nesting, four levels with arrays inside objects inside arrays (jsn-a01); constrained enum + genuinely-null optional field, paired with jsn-t07 where the same nullable field IS present so blanket-nulling cannot score (jsn-a02); conversational instruction inviting prose/fences around the JSON (jsn-a03). Three notes for the harness and scoring: (1) jsn-a03 only measures anything if the harness stores responses raw — no fence-stripping, no preamble-trimming — and the same must hold at scoring time, so a fenced-but-perfect object scores 0 on parseability; recorded in the file's `conventions.raw_capture`; (2) jsn-t12's gold is a **top-level array**, so the scoring comparator must not assume `gold.expected` is a dict — the only case in any file with this shape; (3) rubric §3.5 names the third dimension "enum/constraint conformance", and jsn-h05 leans on the "constraint" half for a stated numeric range rather than an enumerated set — read as in-scope, no rubric change needed. |
| 2026-08-11 | 1 | `cases/extraction.json` written — 20 cases, 12 typical / 5 hard / 3 adversarial, all sources original. Adversarial three: absent fields (ext-a01), ambiguous date + ambiguous currency symbol (ext-a02), near-duplicate field pairs (ext-a03). Schema notes for the remaining three exact-match files: (1) `gold` is `{expected, notes}` where `expected` is the literal object — the summarization `must_include`/`must_not_include`/`reference` shape does not apply; (2) added a file-level `gold_form` and `conventions` block, and restated the conventions inside every `instruction` so each prompt is self-contained; (3) ext-a02 required an `_raw` sibling-field convention so an ambiguous value can be reported without being guessed — the alternative was scoring abstention as a miss, which would punish the correct behaviour; (4) rubric §3.2 gives no anchor for over-abstention (nulling a value that IS determinable), so this is handled in per-case `gold.notes` rather than by touching the frozen rubric — worth a rubric v1.1 changelog entry if the same gap appears in classification or JSON. |
| 2026-08-10 | 0–1 | PRD, rubric v1.0 frozen, decision log (16 decisions), UX & feedback spec, CLAUDE.md, harness spec, test case design + summarization 20 cases. Surface decided: static site + client-side advisor. Feedback: in-page widget → Google Form. |

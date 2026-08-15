# PROJECT STATE — Zero-Budget Model Advisor

> **Read this first.** If you are a fresh chat, agent, or future me picking this project back up, this file is the entry point. It is the single source of truth for where the project stands. Everything else is detail hanging off it.
>
> **Last updated: 2026-08-15 · Phase: 3 of 6 (Run benchmark) · Status: on track, with one timeline constraint — see §7**

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
| 2 · Harness | **Done** | `02-harness/` built and verified: `config.toml`, `runner.py`, `probe.py`, `clients/` (5 providers + shared OpenAI-compatible transport). Resumability, raw capture, backoff accounting and probe gating all tested. |
| 3 · Run benchmark | **Ready to start** | ~1,500 calls → `/03-results`. Gated on the OpenRouter daily cap (§7). |
| 4 · Analysis | Not started | Scoring, κ check, breakeven model, selection memo |
| 5 · Site + advisor | Not started | Static site, client-side advisor, feedback widget |

### Immediate next action

**Phase 2 done.** The harness is built and verified. `python 02-harness/runner.py` runs a preflight (keys present, one authenticated call per provider) and then the matrix; it resumes by default, so an interrupted run is re-entered by re-running the same command. `python 02-harness/probe.py` runs probing, after the benchmark.

**Next: start Phase 3.** Two things to settle first, both recorded in `02-harness/config.toml`:

1. **Confirm the Gemini figures** on the AI Studio rate-limit page — Google's public docs no longer print free-tier RPM/RPD, so `documented_rpm`/`documented_rpd` for `gemini-2.5-flash-lite` are marked CONFIRM rather than carrying a third-party number.
2. **Record per-model terms for the chosen OpenRouter model** (`openai/gpt-oss-20b:free`) — ToS-Review notes OpenRouter's §5.1 model-terms flow-down.

Then resolve open question 1 (judge model) before Phase 4. Note for `/scoring`: three gold shapes now exist across the files — criteria-plus-reference (summarization, rag-qa), literal expected object (extraction, json-output, incl. one top-level array), and label with optional `expected_any` (classification) — plus the `_raw` and `INSUFFICIENT CONTEXT` conventions. Also for `/scoring`: the failure taxonomy is **split by design** — the five transport codes live in `02-harness/clients/base.py`, the three content codes (`REFUSAL`, `MALFORMED`, `HALLUCINATION`) in `04-analysis/scoring/failure_codes.py`. `Scoring-Rubric.md` §6 remains canonical for all eight. See §8 for the per-file notes.

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
               SESSION-STARTUP.md            ← daily startup sequence
               SETUP-AND-TROUBLESHOOTING.md  ← context file for the environment/tooling spoke
               config.toml   ← models, derived pacing, documented limits, probe gating
               runner.py     ← matrix, resumability, record writing. No provider names.
               probe.py      ← rate-limit probing, gated on config `probe_allowed`
               clients/      ← base.py (contract + one retry policy), openai_chat.py
                                (shared wire format), ollama/groq/mistral/openrouter/gemini
  03-results/  (append-only; run-<run_id>.jsonl, probe.jsonl)
  04-analysis/ scoring/failure_codes.py  ← the three content-judgment failure codes
  05-site/     (empty)
```

---

## 4. Decisions that are closed — do not reopen without new information

Full reasoning and challenge-responses live in the **Product Decision Log**. Summary so a fresh chat doesn't relitigate:

**Scope:** Free tiers only, not frontier. Five tasks (summarization, extraction, classification, RAG Q&A, structured JSON). Five providers (Gemini, Groq, OpenRouter, Mistral, Ollama local). **No overall leaderboard** — it would contradict the product's thesis.

**Rejected and settled:** agentic/tool-use suite (free tiers fail outright), multilingual suite (audience too narrow), reasoning/coding benchmarks (commoditised), standalone eval workbench product (crowded market).

**Method:** Rubric frozen before any run. 0–3 scale, no midpoint, unweighted dimensions (the *advisor* handles weighting at query time). LLM-as-judge over all cases, calibrated against 20 hand-scored cases, gated at **quadratic-weighted Cohen's κ ≥ 0.6**. Judge sits **outside** the benchmark set, blinded, order-randomised. Identical untuned prompts across all models. Temp 0, three runs, median. Refusals and errors excluded from quality and reported as failure rates.

**Product:** Static site, client-side advisor over a JSON data file, no backend, no accounts. Quarterly refresh. In-page feedback widget → Google Form. Everything published — rubric, cases, gold answers, judge justifications.

**Test cases:** All source text is **original, authored for this benchmark** — public text risks training-data contamination, which would measure recall rather than comprehension. Gold shape varies by task and is declared per file in `gold_form`; **that branching lives in `/scoring`, never in `/harness`**, which does not read gold at all. Over-abstention is an explicit failure (rubric v1.1) — test sets must pair "correctly refuse" cases with superficially similar answerable ones.

---

## 5. Open questions

| # | Question | Blocks | Owner |
| :---- | :---- | :---- | :---- |
| 1 | Which model is the judge? Must be outside the five under test, and free. | Phase 4 | Braj |
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

- **Timeline — now quantified, and OpenRouter is the binding constraint.** Documented free-tier limits (recorded per model in `config.toml` with source URLs, 2026-08-15): Groq 30 rpm / 1,000 rpd · Gemini ~15 rpm / ~1,000 rpd (CONFIRM) · Mistral 1 rps, no daily cap · **OpenRouter 20 rpm but only 50 requests/day at a zero credit balance.** 300 calls at 50/day is **six days for OpenRouter alone**, against a two-week target. The $10 credit purchase that lifts it to 1,000/day is refused on principle — spending money would invalidate the zero-budget thesis, per the O-1 reasoning. **If the timeline slips, cut models before cutting the human-scored calibration set**; OpenRouter is the natural first cut, and its exclusion would be disclosed. A smaller model set is a scoping decision; an uncalibrated judge is a credibility hole.
- **Rubric defensibility** — mitigated by pre-freeze, published cases, published judge justifications, and an audited disagreement set.
- **Staleness** — mitigated by making refresh cadence part of the product, and by dating every published surface.
- **Scope creep** — the five tasks and five providers are fixed for v1. New task types are a v2 decision.
- **ToS exposure** — rate-limit probing is the legally sensitive part. Terms reviewed per provider first; one account each; no circumvention; a provider that prohibits publication is dropped and the exclusion disclosed.

---

## 8. Session log

| Date | Phase | What happened |
| :---- | :---- | :---- |
| 2026-08-15 | 2 | **Harness built and verified — Phase 2 complete.** `config.toml` (TOML not YAML: `tomllib` is stdlib on 3.11, so the harness stays zero-dependency), `runner.py`, `probe.py`, and six modules under `clients/`. Verified against real Ollama (live resume: killed at 274/300, re-ran, finished at 300 rows with 0 duplicate `(case_id, model_id, run_index)`) and against stub servers for both hosted wire formats. Decisions and findings worth carrying forward: (1) **Prompt assembly** — case files disagree on whether `source` is already restated inside `instruction` (classification, json-output, rag-qa yes; summarization, extraction no), so the runner appends `source` only when its *entire* string is absent. Verified across all 80 cases carrying a source: present exactly once, never doubled. (2) **Failure taxonomy split** — the five transport-determinable codes live in `clients/base.py`, the three content-judgment codes in `04-analysis/scoring/failure_codes.py`; a client setting `REFUSAL` or `HALLUCINATION` would be scoring inside the transport layer. Both modules name `Scoring-Rubric.md` §6 as canonical. (3) **Resumability defaults to resuming** — explicit `--run-id` wins, `--new-run` forces fresh, otherwise the most recent run file is re-entered. A date-derived default was rejected as a defect: a run spanning midnight would re-execute completed work, and the asymmetry is severe (a wrong resume costs one suppressed duplicate; a wrong fresh start costs ~1,500 calls of quota). Startup prints resolved `run_id`, complete and remaining counts. (4) **Provenance** — `git_commit` uses `git describe --always --dirty`; a bare hash recorded against a dirty tree points at code that never existed in any commit, and this benchmark re-runs quarterly for years. Startup warns if provenance is unresolved. (5) **Retry policy is one policy in one place** (`base.py`), shared by all five clients; `openai_chat.py` is purely a wire format. Backoff wait accumulates into `queue_wait_ms` and is provably excluded from `latency_ms` (tested: `Retry-After: 1` → `queue_wait_ms 1000`, `latency_ms 1`). Refusals, timeouts, empty and malformed responses are never retried. (6) **Groq's 403 was Cloudflare, not the key** — error 1010 rejects urllib's default User-Agent before the request reaches the API. All clients now send an identifying `User-Agent`; without it every Groq call would have failed. (7) **Pacing is derived, not invented** — `min_interval_s` computed from each provider's documented rpm with margin, and `documented_rpm`/`documented_rpd`/`documented_source` recorded in config because the results table publishes documented vs measured side by side. (8) **`probe.py` gates on a config flag, never a provider name** — `grep -ic` for all five provider names in `runner.py` and `probe.py` returns 0. Groq and Ollama are `probe_allowed = false`; Groq prints `provenance: documented + incidental` rather than silently disappearing. Stops at 2 consecutive rejections, 24-hour re-probe lock. (9) **Preflight gate** — `.env` is loaded by a 7-line stdlib loader (no `python-dotenv`), all keys checked for presence, and one trivial authenticated call made per provider before the matrix starts; a wrong key would otherwise be recorded as ~300 `API_ERROR` rows and published as a finding about the provider rather than about the setup. (10) **Deferred classification is the general pattern** — the harness records `error_raw` verbatim and classifies provisionally (the loose `"quota"` substring match for the retry decision, `_period` in probe.py); **Phase 4 must audit every `RATE_LIMIT` row's `error_raw` and reclassify from observed provider strings before publishing.** Open for confirmation: Gemini's documented figures (AI Studio, docs page no longer prints them) and the two model picks — `mistral-small-2603` chosen over `-latest` for reproducibility, `openai/gpt-oss-20b:free` as the most general-purpose of 16 free OpenRouter models. |
| 2026-08-11 | 1 | `cases/rag-qa.json` written — 20 cases, 12 typical / 5 hard / 3 adversarial, all passages original. 70 passages total, 3–5 per case, every case carrying at least one irrelevant or only-tangentially-relevant passage because that is what real retrieval returns. Three notes for the harness and scoring: (1) an explicit abstention channel — the exact token `INSUFFICIENT CONTEXT` plus a final `Citations:` line — is offered on **all 20 cases**, following the classification `Note:` precedent in Test-Case-Design §2: abstention (rubric §3.4) is unmeasurable without a sanctioned, parseable way to express it, and offering it only on the unanswerable cases would let the instruction signal which cases are traps. Scoring must parse the last line as citations and the body for the abstention token. (2) `gold` is criteria-plus-reference with two RAG-specific keys — `gold.supported_by` (passage IDs that actually support the answer; **empty list on the two abstention cases**, where the only correct citation line is `Citations: none`) is the ground truth for citation accuracy and is scored independently of whether the answer text was right. (3) Passage IDs are **local to each case** (P1, P2, …) and must never be compared across cases. Adversarial three: an unanswerable erasure-timeline question surrounded by plausible retention numbers that answer adjacent questions (rag-a01); a 99.9% vs 99.5% uptime figure contradicted between a pricing page and an MSA schedule with no stated precedence, where naming both and the absence of a precedence rule scores 3 and asserting that the contract supersedes the marketing copy is a groundedness failure because the passages never say so (rag-a02); a Documents-module file-size question whose only size figure belongs to a deprecated, separate-store Attachments widget, testing topic-similarity matching against actual relevance (rag-a03). Per rubric §3.4, rag-a01 is paired with **two** answerable cases in the same domain, register and question shape — rag-t05 (explicit, single passage) and rag-t11 (answerable only via a two-passage inference, so it is the case most likely to draw a false abstention); the adversarial sub-score must be read together with that pair, since a model scoring 3 on a01 and 0 on t05/t11 has learned caution, not judgment. Also note rag-h03, which splits the abstention dimension inside a single case — half the question is answerable and half genuinely is not, so blanket `INSUFFICIENT CONTEXT` scores 1, not 3 — and rag-h05, which is supersession (dated, stated) rather than contradiction, so hedging it like a02 is over-hedging. No rubric change needed: v1.2 §3.4 and §3.6 covered every case, including the empty-`supported_by` shape. |
| 2026-08-11 | 1 | `cases/classification.json` written — 20 cases, 12 typical / 5 hard / 3 adversarial, all sources original. Five label sets rotate across the file (sentiment, support routing, intent, priority, content category) so no model can succeed by memorising one taxonomy; every `instruction` states its complete permitted set inline and repeats the source verbatim, so each prompt is self-contained. Three notes for the harness and scoring: (1) a uniform output convention — label on line one, optional second line beginning `Note:` — is offered on **all 20 cases**, not just the ambiguous ones, because ambiguity handling (rubric §3.3) is unmeasurable without a sanctioned channel for uncertainty, and offering it selectively would let a model pass by reading the instruction rather than the input; scoring must therefore parse line one for correctness/validity and line two for ambiguity handling. (2) Two cases have no single gold label and use `gold.expected: null` plus `gold.expected_any: [...]` — the comparator must handle this shape; it is the classification analogue of extraction's `_raw` escape hatch. (3) cls-a02 scores only **two** of the three dimensions — label correctness is not-applicable and must be recorded as such, not as a miss, since no permitted label is right. Adversarial three: genuine Billing/Technical boundary where the bare-label answer scores 1 and naming the alternative scores 3 (cls-a01); a research enquiry against a four-label set with the `Other` escape deliberately removed, where returning "Other" is the failure (cls-a02); a polite, self-blaming report of eleven thousand deleted clinical records, gold P1, deliberately paired with typical case cls-t10 — a furious message about a wrong name in a PDF footer, gold P4 — so a tone-following model gets both wrong and the pair is read together in the adversarial sub-score. No rubric change needed: §3.3's three dimensions covered every case without amendment. |
| 2026-08-11 | 1 | `cases/json-output.json` written — 20 cases, 12 typical / 5 hard / 3 adversarial, all sources original. This file measures **format reliability, not content difficulty**: sources are deliberately short and unambiguous so failures attribute to structure, and schema complexity is the variable that moves (flat → mixed types → nested → arrays of scalars → arrays of objects → nullable → enums → top-level array). Every instruction carries the full schema inline. Adversarial three: deep nesting, four levels with arrays inside objects inside arrays (jsn-a01); constrained enum + genuinely-null optional field, paired with jsn-t07 where the same nullable field IS present so blanket-nulling cannot score (jsn-a02); conversational instruction inviting prose/fences around the JSON (jsn-a03). Three notes for the harness and scoring: (1) jsn-a03 only measures anything if the harness stores responses raw — no fence-stripping, no preamble-trimming — and the same must hold at scoring time, so a fenced-but-perfect object scores 0 on parseability; recorded in the file's `conventions.raw_capture`; (2) jsn-t12's gold is a **top-level array**, so the scoring comparator must not assume `gold.expected` is a dict — the only case in any file with this shape; (3) rubric §3.5 names the third dimension "enum/constraint conformance", and jsn-h05 leans on the "constraint" half for a stated numeric range rather than an enumerated set — read as in-scope, no rubric change needed. |
| 2026-08-11 | 1 | `cases/extraction.json` written — 20 cases, 12 typical / 5 hard / 3 adversarial, all sources original. Adversarial three: absent fields (ext-a01), ambiguous date + ambiguous currency symbol (ext-a02), near-duplicate field pairs (ext-a03). Schema notes for the remaining three exact-match files: (1) `gold` is `{expected, notes}` where `expected` is the literal object — the summarization `must_include`/`must_not_include`/`reference` shape does not apply; (2) added a file-level `gold_form` and `conventions` block, and restated the conventions inside every `instruction` so each prompt is self-contained; (3) ext-a02 required an `_raw` sibling-field convention so an ambiguous value can be reported without being guessed — the alternative was scoring abstention as a miss, which would punish the correct behaviour; (4) rubric §3.2 gives no anchor for over-abstention (nulling a value that IS determinable), so this is handled in per-case `gold.notes` rather than by touching the frozen rubric — worth a rubric v1.1 changelog entry if the same gap appears in classification or JSON. |
| 2026-08-10 | 0–1 | PRD, rubric v1.0 frozen, decision log (16 decisions), UX & feedback spec, CLAUDE.md, harness spec, test case design + summarization 20 cases. Surface decided: static site + client-side advisor. Feedback: in-page widget → Google Form. |

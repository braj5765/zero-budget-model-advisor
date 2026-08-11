# PRD — Zero-Budget Model Advisor

| Field | Fill in |
| :---- | :---- |
| **Feature / Initiative** | Zero-Budget Model Advisor — free-tier LLM benchmark + routing advisor |
| **Owner (PM)** | Braj |
| **Status** | Draft |
| **Last updated** | 2026-08-10 |
| **Epic** | [ link ] |
| **Design / prototype** | [ link ] |
| **Eng "how" doc** | [ link ] |

---

### 1. Description

An original, independently-run benchmark of free and near-free LLM tiers across five everyday builder tasks, published as a quarterly-refreshed public index — plus an advisor on top of it that takes a user's volume, latency SLA and quality bar and returns a recommended model stack with cost projections and a paid-tier breakeven point.

---

### 2. Problem

- Every published benchmark measures flagship, paid models. Nobody has rigorously measured what you can actually ship on a free tier.
- The variables that decide whether a free tier works — real rate-limit ceilings, p95 latency under those limits, and where quality genuinely breaks — are undocumented.
- Builders with no budget therefore pick a model blind, discover the ceiling in production, and re-architect under pressure.
- There is no way to answer "at what volume does paying start to make sense?" with data.

---

### 3. Why / Why now

- Free tiers are now good enough to ship real products on, but the boundary of "good enough" is unmapped — the gap only became interesting recently.
- The zero-budget constraint is the thesis, not a limitation: benchmarking frontier models costs money and duplicates vendor work; benchmarking free tiers is free to produce and genuinely novel.
- The 2026 AI PM bar treats cost and latency as first-class roadmap variables alongside quality. This project produces evidence of that judgment — eval design, failure-mode analysis, tradeoff framing — rather than claims of it.
- Free-tier terms shift constantly, which makes a recurring index defensible as a product rather than a one-off report.

---

### 4. Audience

- **Indie builders and solo founders** shipping on zero budget who need to know which free tier survives their workload.
- **Students and learners** building portfolio projects who can't put a card on file.
- **Early-stage teams** prototyping before a spend decision, who need the breakeven point to justify moving to paid.
- **Secondary: hiring managers and AI PM peers** evaluating the methodology itself.

---

### 5. What

**Requirements (user stories)**

- As a builder, I want to describe my use case (task type, monthly volume, latency SLA, quality bar), so that I get a ranked model recommendation instead of guessing.
- As a builder, I want to see real measured rate-limit ceilings per provider, so that I know whether my volume fits before I build on it.
- As a builder, I want p95 latency measured under those rate limits, so that my SLA estimate reflects real conditions rather than a single warm call.
- As a builder, I want to see documented failure modes per model per task, so that I can design fallbacks instead of discovering breakage in production.
- As a builder, I want a cost projection and a paid-tier breakeven point, so that I know when free stops being the right answer.
- As a skeptical reader, I want the scoring rubric and test cases published openly, so that I can audit or reproduce the results.
- As a returning reader, I want each index dated and versioned, so that I know how stale the data is.

**Scope (fixed)**

- Tasks: summarization, extraction, classification, RAG Q&A, structured JSON output reliability.
- Models: Gemini free tier, Groq, OpenRouter free models, Mistral free tier, one local model via Ollama.
- Measures: rubric quality score, p95 latency, real rate-limit ceiling, failure modes, cost projection, breakeven.

**Tickets (in build order)**

| # | Ticket | Summary |
| :---- | :---- | :---- |
| 1 | — | Fix the model set; confirm free-tier terms and limits per provider |
| 2 | — | Write the scoring rubric (separate artifact) — before any run |
| 3 | — | Build ~20 test cases per task (100 total) with gold references |
| 4 | — | Build the internal eval harness (runner, logging, rate-limit probing) |
| 5 | — | Run the benchmark; capture quality, latency, limits, failures |
| 6 | — | Analyse results; write the model-selection memo and tradeoff framework |
| 7 | — | Build the advisor surface (inputs → recommended stack + cost projection) |
| 8 | — | Publish the index v1 and set the quarterly refresh cadence |

**Assumptions to validate**

- Free tiers permit benchmarking and publication of results under their ToS.
- Rate-limit ceilings can be measured empirically without account suspension.
- ~20 cases per task is enough to separate models meaningfully rather than surface noise.
- Rubric scoring is reproducible — the same case scored twice lands the same way.
- Users can articulate volume, latency SLA and quality bar well enough for the advisor to route on.

---

### 6. How

**Owned by engineering — left blank until the doc is walked through.** (Solo project: fill in after the eval harness spike.)

*Approach:* [ ... ]

**Spikes needed?**

- [ ] How to probe real rate-limit ceilings safely without tripping abuse detection
- [ ] Judge agreement: does LLM-as-judge match human scores on the calibration subset closely enough (target κ ≥ 0.6) to trust the automated remainder?

---

### 7. When

|  | Fill in |
| :---- | :---- |
| **Target** | 2 weeks from kickoff (2026-08-10 → 2026-08-24) · two 1-week sprints |
| **First version** | Rubric + 100 test cases + full benchmark run + published index with static recommendations |
| **Deferred to later** | Interactive advisor UI, quarterly refresh automation, expanded model set, agentic/multilingual task suites |

---

### Risks

- **Staleness** — free-tier terms change fast; mitigated by the quarterly refresh cadence being part of the product, not an afterthought.
- **Scope creep on the task suite** — five tasks are fixed; new task types are a v2 decision.
- **Rubric defensibility** — the rubric is written and published before any run, and is the artifact most likely to be challenged.

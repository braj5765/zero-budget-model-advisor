# Model Selection Memo — free-tier LLMs, v1 index

**2026-08-29 · Braj · Data: 1,500 benchmark calls, 1,200 judged responses, rubric v1.7, judge `minimax-m3` (κ=0.650 vs human calibration)**

**Audience:** a builder with no budget choosing what to ship on. **This memo does not name a best model, because the data does not support one.**

---

## 1. The one-paragraph answer

There is no dominant free tier. **Groq is 3–5× faster than everything else and the only hosted option that holds up on structured JSON. Gemini is the strongest on comprehension tasks — classification, RAG, summarization — and the most robust under adversarial input. Mistral matches the field on text tasks and collapses entirely on JSON. Ollama costs nothing forever and is 10–40× slower, which rules it out of anything interactive.** Which of those matters is a property of your workload, not of the models, and that is why this index ships an advisor rather than a ranking.

---

## 2. What the data actually says

### 2.1 Structured JSON is where free tiers break — and it is the task builders assume is safe

| Model | JSON score | `n/a` count | Text-task range |
| :---- | ---: | ---: | :---- |
| Groq Llama-3.3-70b | **87.5** | 6 | 75.4 – 96.7 |
| Ollama Llama-3.2-3b | 75.8 | 9 | 57.8 – 72.9 |
| Gemini 3.5 Flash Lite | 67.1 | 18 | 88.3 – 96.2 |
| Mistral Small | **33.8** | **39** | 82.5 – 90.8 |

Every model scores materially worse on JSON than on its own text tasks, and the `n/a` counts say why: an unparseable response scores 0 on parseability and leaves its content dimensions unscoreable (rubric §3.5). Mistral produced 39 unscoreable dimension-slots — roughly half the task — while scoring 82–91 on prose.

**This is the finding with the most practical consequence.** Structured output is the first thing most builders wire into an app and the thing they assume is mechanical. A model that writes excellent prose can be close to unusable behind a JSON schema, and nothing on a vendor page tells you that.

*Note the direction of the `n/a` rule: excluding unscoreable dimensions* raises *a mean. Mistral scored 33.8 after that exclusion.*

### 2.2 Temperature 0 is not deterministic

Share of dimension scores identical across three runs at temperature 0:

| Task | Groq | Ollama | Gemini | Mistral |
| :---- | ---: | ---: | ---: | ---: |
| Summarization | **36.2%** | 45.0% | 58.8% | 60.0% |
| Extraction | 86.2% | 67.5% | 81.2% | 86.2% |
| RAG Q&A | 93.8% | 76.2% | 90.0% | 86.2% |
| JSON | 95.9% | 91.5% | 79.0% | 92.7% |

On the majority of summarization cases, three identical requests at temp 0 produced responses that scored differently. **Free-tier serving is not reproducible**, presumably through batching, routing and quantisation the builder cannot see or control. Anyone building a regression suite against a free tier on the assumption that temp 0 is stable will get flapping tests and blame their own code.

Constrained tasks are far more stable than generative ones — which is intuitive in hindsight and, as far as I can find, not published anywhere with numbers attached.

### 2.3 Adversarial performance separates models that look equivalent in aggregate

| Task | Aggregate spread | Adversarial spread |
| :---- | :---- | :---- |
| Extraction | 72.9 – 92.5 (19.6) | **44.4 – 75.0 (30.6)** |
| Summarization | 75.4 – 88.3 (12.9) | **58.3 – 77.8 (19.5)** |

Aggregate scores cluster; adversarial scores fan out. Groq and Gemini differ by 0.4 points on extraction overall and by 5.5 on the adversarial slice; on summarization Groq drops 17 points under adversarial input while Gemini drops 10.5 and Ollama *rises*.

**Practical reading:** aggregate quality tells you how a model behaves on your happy path. The adversarial sub-score tells you how it behaves on the inputs that will actually hurt you — sources inviting a false causal inference, documents where a field is genuinely absent, questions the context cannot answer. Those are 3 cases in 20 here, and they carry most of the discriminative signal.

### 2.4 Latency is a category difference, not a percentage

p95, milliseconds:

| Model | Best task | Worst task |
| :---- | ---: | ---: |
| Groq | 577 | 1,797 |
| Mistral | 889 | 3,171 |
| Gemini | 1,577 | 4,515 |
| Ollama (local CPU) | 17,359 | **81,703** |

Groq is roughly 3× faster than Gemini and 30–45× faster than local CPU inference. **Local is not a slower version of hosted; it is a different product.** An 82-second p95 excludes it from anything a user waits on, and includes it in anything batch — overnight enrichment, backfills, offline processing — where its zero marginal cost and absent rate limit dominate everything else.

### 2.5 Reliability belonged entirely to the excluded provider

All four scored models: **100% success across 300 calls each.** Zero refusals, zero timeouts, zero malformed transport failures.

OpenRouter, cut from quality scoring: **96/300 (32%)**, 204 `RATE_LIMIT`. Two distinct ceilings — a documented 50/day account cap that proved accurate, and an undocumented **shared-pool** ceiling that rejected after two requests on a fresh daily quota. The second is the important one: it is not the builder's quota at all, but contention across every free-tier user of that pool. Availability that depends on other people's traffic.

Groq contributes the one incidental finding: 8 retries across 7 rows, including a **1,075-second backoff** on a `Retry-After` Groq itself sent. All eventually succeeded, so it does not appear in the failure rate — but a builder with a 30-second SLA would have seen those as failures.

---

## 3. Recommendations by workload

| If your workload is… | Use | Because | Fall back to |
| :---- | :---- | :---- | :---- |
| **Interactive, user-waiting** | **Groq** | 577ms p95; nothing else is in the same class | Mistral (889ms) |
| **Structured JSON output** | **Groq** | 87.5 with only 6 `n/a`; the only hosted tier that holds | Gemini (67.1) — **never Mistral (33.8)** |
| **Comprehension: RAG, classification, summarization** | **Gemini** | 88–96 across all three, best adversarial robustness | Groq for RAG (96.7); Mistral for summarization (82.5) |
| **High volume, latency-tolerant** | **Mistral** | 60 rpm, no documented daily request cap; ceiling is token-based (1B/month) | Gemini/Groq at 1,000 rpd each |
| **Batch, offline, unlimited** | **Ollama** | No quota, no cost, no third party. 72–76 on most tasks | — |
| **Anything where availability matters** | **Not OpenRouter free** | 32% success; shared-pool ceiling outside your control | Any of the four above |

**Every recommendation assumes a fallback.** Free tiers fail — Groq waited 1,075 seconds under its own instruction, and OpenRouter failed two calls in three. A single-provider design on a free tier is not a design.

---

## 4. When free stops being the answer

The binding constraint differs by provider, and that determines your breakeven:

| Provider | Binding constraint | Runs out when |
| :---- | :---- | :---- |
| Gemini | 1,000 requests/day | volume > ~1,000/day |
| Groq | 1,000 requests/day | volume > ~1,000/day |
| Mistral | 1B tokens/month, 60 rpm | token volume, not request count |
| Ollama | wall clock | throughput > ~1 request/40s sustained |
| OpenRouter free | shared-pool contention | unpredictably, at any volume |

**There is no single free-tier ceiling. There are two classes, and they differ by roughly 65×.**

- **Request-capped tiers (Gemini, Groq): ~1,000 requests/day.** About 40/hour sustained, or one request every 90 seconds. This is the number most people mean by "the free tier limit."
- **Token-capped tiers (Mistral): ~65,198 extraction requests/day**, derived from 1B tokens/month against the mean tokens-per-request measured in this benchmark. Not a documented figure — computed from our own token counts, and **it differs by task**, because extraction prompts are longer than classification ones.

*Corrected 2026-08-29.* An earlier version of this section gave ~1,000/day as the practical hosted ceiling generally. That is right for the request-capped tiers and wrong by a factor of ~65 for the token-capped one, and the error came from treating the metering unit as incidental rather than as the thing that determines the answer.

**Consequence for a builder:** if your volume sits between roughly 1,000 and 65,000 requests/day, you are not out of free tiers — you are out of *request-capped* ones, and the decision is to move to a token-metered provider rather than to start paying. That band is wide and is where most growing side projects live.

Note also that Mistral's two constraints nearly coincide: ~65,198/day averages ~45 requests/minute against a documented 60 rpm cap. Sustained volume near the token ceiling leaves almost no headroom for bursts, so in practice the rate limit binds first for anything spiky.

*Rupee/dollar breakeven figures are deliberately not stated here, or anywhere in this index.* Paid pricing changes faster than this index refreshes, and a stale cost figure is worse than none because the reader acts on it. This memo fixes the **volume thresholds**, which are the part the benchmark actually measured; the advisor names which paid path removes the binding constraint, and the reader prices it against the vendor's current page. *Corrected 2026-08-29: this paragraph previously stated that "the advisor computes breakeven from live pricing at query time." It does not and cannot — the site is static with no backend (Decision C1), and `advisor.js` has never contained a price. See Decision C5.*

---

## 5. What I would not conclude from this data

- **That any of these numbers are precise.** n = 20 cases per task. Differences under ~5 points are not claimed as meaningful. Adversarial sub-scores rest on n = 3 and are directional signal, not measurement.
- **That these results generalise to tuned prompts.** Every model got the same untuned prompt, deliberately (Decision B4). A model that responds well to tuning is undersold here.
- **That they will hold next quarter.** Free tiers move. Every figure is dated; the index refreshes quarterly for exactly this reason.
- **That the judge is neutral.** κ = 0.650 against 76 human-scored dimensions clears the 0.6 gate, but the margin is thin and the interval is wide. Four ≥2-point human/judge disagreements remain, audited and published.
- **That Mistral is bad at JSON in general.** It is bad at JSON *under this prompt, untuned, at this date*. That is exactly what a builder gets out of the box, which is why it is reported — but it is a narrower claim than "Mistral can't do JSON."

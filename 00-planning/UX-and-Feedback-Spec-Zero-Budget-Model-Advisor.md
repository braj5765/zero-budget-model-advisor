# UX & Feedback Spec — Zero-Budget Model Advisor

**v1.0 · 2026-08-10 · Owner: Braj**

Surface decision: **one static site — published index + client-side advisor**. No backend, no accounts, no server-side keys. All benchmark data ships as a versioned JSON file the page reads at load.

---

## 1. The core UX principle

Two audiences arrive with opposite intents, and the site must not force either through the other's path:

- **The decider** wants an answer in under 60 seconds: "what should I use?" → straight to the advisor.
- **The skeptic** wants to know whether the answer is trustworthy → straight to the data and the method.

So: **the advisor is the front door, and every recommendation is a door into the evidence.** No recommendation is ever shown without the reasoning and the underlying numbers one click away. This is also the design decision that best demonstrates PM judgment — the product's structure enacts its thesis that measurement without transparency isn't worth trusting.

---

## 2. Site structure

Five routes, one page each. Deliberately small.

| Route | Purpose | Primary audience |
| :---- | :---- | :---- |
| `/` — **Advisor** | Describe your use case → ranked recommendation with cost projection | Decider |
| `/results` | Full interactive results table across models × tasks × dimensions | Skeptic, browser |
| `/model/:id` | Per-model profile: scores, failure modes, latency, limits, verdict | Comparison shopper |
| `/methodology` | Rubric, test-case design, judging protocol, κ results, limitations | Skeptic, interviewer |
| `/about` | Why this exists, refresh cadence, changelog, how to contribute | All |

---

## 3. The Advisor flow

**Four inputs, progressively disclosed, one screen. No wizard, no multi-step form** — a builder abandoning at step 3 of 5 is the main failure mode to design against.

1. **What are you building?** — task type picker (the five tasks; multi-select allowed, since real apps mix them)
2. **Volume** — requests/day slider, with plain-language anchors ("~side project", "~small app", "~production")
3. **Latency need** — three options: *doesn't matter* / *interactive (<3s)* / *real-time (<1s)*
4. **Quality bar** — *rough draft is fine* / *needs to be right* / *user-facing, errors are costly*

**Optional advanced:** per-dimension weighting sliders (faithfulness vs coverage vs concision, etc.). Collapsed by default — this is the honest expression of decision B2, and hiding it behind a toggle keeps the default path fast without pretending weighting doesn't matter.

### Output — the Recommendation card

Three stacked results, ranked, each showing:

- **Model + provider**, with a one-line plain-English verdict ("Best quality at your volume, but you'll hit the ceiling above ~800 req/day")
- **Fit bars** for quality / latency / headroom against the user's stated volume
- **Cost projection** — free at this volume, or ₹/$ per month if they exceed the tier
- **Breakeven callout** — "free until ~X req/day; above that, paid tier Y costs less than the workarounds"
- **Known failure modes** for their selected tasks, stated as design guidance, not warnings
- **"Why this?"** expander → the exact scores, n, judge version and measurement date behind the ranking

### Three UX rules that are really product decisions

- **Always show a fallback pairing.** Every recommendation includes a suggested secondary model and the trigger condition for failing over to it. Free tiers *will* fail; a recommendation that ignores that is incomplete, and fallback design is core AI PM vocabulary.
- **Never hide the date.** Every results surface carries "measured on [date] · judge [model+version]" in the header. Stale data must degrade visibly.
- **Say "none of these fit."** If the user's volume or latency need exceeds every free tier, the advisor says so and names the cheapest paid option. A tool that always finds an answer isn't advising, it's flattering.

---

## 4. Results page

- Sortable, filterable matrix: models (rows) × tasks (columns), cell = quality score with a failure-rate badge.
- Toggle between **quality**, **p95 latency**, **success rate**, and **rate-limit ceiling** views — the same grid, four lenses, which is how the cost/latency/quality tradeoff becomes visible rather than asserted.
- Expand any cell → per-dimension breakdown, adversarial sub-score, sample outputs, and the judge's written justification.
- Persistent, non-dismissible note: *no overall ranking is published, and why* — linking to decision A4.

---

## 5. Feedback mechanism

**In-page widget → Google Form/Sheet backend.** Zero cost, no backend, structured and analysable.

### Design principle

Feedback is collected **at the moment of judgment, not at the bottom of the page.** A generic "leave feedback" footer collects nothing. Three specific prompts at three specific moments:

| Placement | Prompt | Captures |
| :---- | :---- | :---- |
| Under the Recommendation card | *Was this useful?* → 👍 / 👎, then one optional free-text line | Advisor usefulness, per input-combination |
| On any expanded score cell | *Disagree with this score?* → short form: which dimension, what you'd score it, why | Rubric disputes — the highest-value input this project can receive |
| `/about` and results footer | *What should we measure next?* → model requests, task requests | Roadmap signal for the next quarterly refresh |

### Data captured per submission

Timestamp, page/route, anonymised session ID (client-generated, not persisted across visits), the advisor inputs that produced the recommendation (so 👎 responses are diagnosable rather than just discouraging), the free-text response, and index version. **No PII, no accounts, no third-party analytics.** The privacy stance is itself a stated product decision, not an oversight.

### What the feedback is actually for

Three questions v1 needs answered, and the instrumentation exists to answer them specifically:

1. **Does the advisor change decisions?** — the success metric from the decision log. Captured via an optional follow-up on 👍: *"did this change what you were going to use?"*
2. **Is the rubric defensible in the wild?** — measured by the volume and substance of score disputes. Disputes are a feature; silence would mean nobody is reading closely.
3. **What's missing?** — model and task requests, which directly feed the next refresh's scope decision.

### The loop that closes

Feedback that changes nothing trains people to stop giving it. So: **every quarterly refresh ships a changelog entry naming what feedback changed** — models added, rubric anchors sharpened, scores revised after a dispute. Disputes that led to a re-score get a public note. This is cheap, and it's the difference between a feedback form and a feedback mechanism.

---

## 6. What is deliberately not in v1

Stated so the omissions read as choices rather than gaps: user accounts, saved comparisons, shareable result URLs, a public API, email capture, dark mode, mobile-optimised advisor beyond basic responsiveness, and third-party analytics. Each is a v2 candidate; none is load-bearing for the thesis, and all of them cost time that belongs to the benchmark run.

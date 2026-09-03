# Product Decision Log — Zero-Budget Model Advisor

**v1.0 · 2026-08-10 · Owner: Braj**

The purpose of this document is not to record what I built. It is to record **what I chose, what I chose against, and what would change my mind** — so that when any of it is challenged, the answer is a position rather than an improvisation.

Format for each decision:
**D — the decision · A — the alternative rejected · R — the reasoning · C — the challenge I expect · M — what would change my mind.**

A decision without a stated "what would change my mind" is a belief, not a judgment. Every entry has one.

---

## Part A — Scope decisions

### A1. Benchmark free tiers, not frontier models

- **D:** Measure only free and near-free tiers.
- **A:** Benchmark GPT/Claude/Gemini flagships like everyone else.
- **R:** Vendor and academic benchmarks already saturate the frontier. Nobody publishes what you can actually ship on a free tier — where limits bite, what latency looks like under them, where quality breaks. The constraint produces the novelty; it isn't a compromise around it.
- **C:** *"Isn't this just a budget excuse?"*
  → The output is a dataset that does not currently exist, aimed at an audience — indie builders, students, pre-spend teams — that existing leaderboards actively fail. If I had a budget I would still choose this, because the frontier version has nothing to add.
- **M:** If a credible free-tier benchmark with real rate-limit and latency data published first, I'd differentiate on task realism or refresh cadence rather than duplicate it.

### A2. Five tasks, fixed

- **D:** Summarization, extraction, classification, RAG Q&A, structured JSON.
- **A:** Agentic/tool-use suite; Indic/multilingual suite; reasoning and coding benchmarks.
- **R:** These five are the actual composition of everyday builder workloads, and recommendations are only meaningful if the benchmarked tasks resemble the reader's real work. Agentic tasks were rejected because free tiers frequently fail them outright — a table of zeroes is not information. Multilingual was differentiated but narrows the audience below the point where the index is worth maintaining. Reasoning and coding are commoditised by public leaderboards.
- **C:** *"Agentic is where the industry is going — why ignore it?"*
  → Agreed on direction, but v1 measures what this audience ships **today**. A suite that mostly returns failures tells a builder nothing actionable. It's a v2 candidate once free tiers support tool use reliably, and it's on the roadmap for that reason.
- **M:** If a pilot run showed ≥3 of the 5 free tiers completing basic tool-use tasks at >70% success, agentic moves into scope.

### A3. Five providers, one of them local

- **D:** Gemini free tier, Groq, OpenRouter free models, Mistral free tier, one local via Ollama.
- **A:** A wider provider sweep.
- **R:** These cover the structurally distinct options: a hyperscaler free tier, a speed-optimised inference host, an aggregator, an open-weights vendor, and self-hosted. Adding a sixth aggregator adds rows, not insight. Ollama is included specifically because "run it yourself" is the true floor of zero-budget and needs a measured comparison point rather than folklore.
- **C:** *"Your sample is too small to generalise."*
  → I don't generalise. I publish per-model results with n stated, and the advisor routes across measured options only. No claim is made about unmeasured models.
- **M:** Provider set is re-opened every quarterly refresh; it's explicitly a living list.

**Resolved 2026-08-13:** OpenRouter's terms state credit purchase is required to make API calls (minimum $5), which would have disqualified it — the zero-budget constraint is the thesis, and spending $5 to test it would invalidate the premise rather than bend it. Verified empirically instead: a `:free` model returns a successful completion on a zero balance. **OpenRouter stays; model set is five.** The documented-vs-actual gap is published in its model profile, flagged as undocumented behaviour that can be withdrawn without notice, and re-verified each refresh.

### A5. OpenRouter cut from scoring after the run, its failure data published

- **D:** After the benchmark returned **96 successes in 300 attempts (68% `RATE_LIMIT`) over 19.4 hours**, OpenRouter was removed from quality scoring. The index scores four models. Its 204 `RATE_LIMIT` rows stay in `/03-results` and feed the failure-rate table, the rate-limit findings, and its model profile.
- **A:** (i) Keep it and score on 96 responses — but median-of-three over 100 cases is impossible at that coverage and the 12/5/3 stratification collapses, so the scores would be uncomparable to the other four while *looking* comparable. (ii) Spend six days re-running to fill coverage — the documented 50/day cap makes 300 calls a six-day job, against a two-week total budget. (iii) Delete it and say nothing.
- **R:** Pre-registered in §7: *if the timeline slips, cut models before cutting the calibration set.* This is that rule firing, not an improvisation. Option (i) publishes a number the method can't support; option (iii) hides the single most useful thing measured about OpenRouter.
- **C:** *"Isn't dropping a provider that performed badly exactly the bias your rubric is supposed to prevent?"*
  → It would be, if quality had been the reason. It wasn't — OpenRouter was cut for **insufficient coverage to score fairly**, and the cut is *adverse to it*: the failure rate, the daily cap, and the shared-pool ceiling are all published in full. The decision rule was written before the data existed, and the raw rows are in an append-only file anyone can check.
- **M:** If a later refresh achieves ≥95% coverage within the run window, OpenRouter returns to quality scoring. Nothing about it is permanently excluded.

**Two findings retained and published:**

1. **Two distinct ceilings, and the second is the real story.** Benchmark 429s carried `limit_source: openrouter_free_tier_daily` (`X-RateLimit-Limit: 50`) — the account's own documented cap, which proved accurate. The probe, on a fresh daily quota, was rejected after **two requests** with `limit_source: upstream_provider_shared_pool`. That is not the builder's quota at all; it is contention across every free-tier user, and it is undocumented, unpredictable, and outside the builder's control. It explains the 68% failure rate better than the daily cap does. **A free tier whose availability depends on other people's traffic** is the finding, and it is more useful to the audience than any quality score would have been.
2. **O-1 stands:** `:free` models are callable at a zero credit balance despite terms stating credits are required.

**Correction, logged rather than quietly fixed (2026-08-16):** an earlier version of this entry claimed OpenRouter's documented 50/day was "contradicted in both directions," citing 241 calls on 15 Aug. That conflated *attempts* with *successes* — 241 attempts, 194 rejected, 47 served. Successes per day were 47 and 49 against a documented 50. **OpenRouter's documented limit is accurate**, and the corrected finding is narrower: a 50/day cap makes a 300-call benchmark a six-day job, which is what forced the cut. *Attempts vs successes must be distinguished everywhere in the analysis.* The correction is recorded here because a decision log that only contains conclusions its author still likes is not evidence of judgment.

### A4. No overall "best model" leaderboard

- **D:** Publish per-task, per-dimension results; refuse a single composite ranking.
- **A:** A headline leaderboard — far more shareable.
- **R:** A composite number would directly contradict the product's thesis, which is that the right model depends on the reader's volume, latency SLA and quality bar. Publishing one would get more traffic and make the advisor pointless.
- **C:** *"You're leaving reach on the table."*
  → Yes, deliberately. The credibility of the index is the asset; a rank-1 model that's wrong for most readers spends that credibility for traffic.
- **M:** Nothing short of the tradeoffs collapsing — i.e. one model dominating on every dimension simultaneously, in which case the leaderboard would be the honest finding.

---

## Part B — Methodology decisions

### B1. Rubric frozen before any model ran

- **D:** Rubric written, versioned, and published pre-run; changes require a changelog entry and re-scoring.
- **R:** A rubric authored after seeing results can be shaped to fit them, and the shaping is usually unconscious. Freezing is the only structural defence.
- **C:** *"How do I know you didn't tweak it?"*
  → Version-controlled with timestamped commits predating the run data, and a changelog that records every post-freeze change with its reason.
- **M:** Nothing. This is the load-bearing discipline of the whole project.

### B2. 0–3 scale, unweighted dimensions

- **D:** Four-point scale, no midpoint; task score is the unweighted mean of dimensions.
- **A:** 1–5 or 1–10; weighted dimensions.
- **R:** Finer scales manufacture false precision and inflate inter-rater variance without adding signal; a midpoint is where ambiguous cases go to hide. Weighting is an unargued assumption about what the reader values — so the **advisor** lets the user weight at query time, which is strictly better than me guessing once for everyone.
- **C:** *"Faithfulness surely matters more than concision."*
  → For you, probably. That's precisely why weighting is a user input and the per-dimension breakdown is always published, never just the mean.
- **M:** If user feedback shows nobody adjusts the weights, a sensible default weighting ships in v2 — as a default, still overridable.

### B3. LLM-as-judge, calibrated against 20 human-scored cases

- **D:** Judge scores all cases; I hand-score a 20% stratified subset; quadratic-weighted Cohen's κ ≥ 0.6 gates acceptance.
- **A:** Score all 500+ judgments by hand (defensible, doesn't fit 2 weeks); trust the judge uncalibrated (fits, indefensible).
- **R:** The hybrid buys scale while keeping a measurable, reportable check on it. The κ number turns "trust me" into a figure a critic can attack on its merits.
- **C:** *"LLM judges are biased and you know it."*
  → Correct, and I've stated the residual risk rather than hidden it. Controls: the judge sits **outside** the benchmark set (no self-scoring), responses are blinded and order-randomised, every score carries a written justification, and every ≥2-point human/judge disagreement is audited and published. If κ misses 0.6, that task gets hand-scored and I say so.
- **M:** If κ came in below 0.6 across most tasks, the judge approach is abandoned for a smaller hand-scored benchmark. Fewer models, real scores.

### B4. Identical, untuned prompts across all models

- **D:** One prompt per test case, used verbatim everywhere.
- **A:** Optimise the prompt per model.
- **R:** Per-model tuning measures my prompt engineering as much as the model, and it isn't reproducible by a reader. Out-of-the-box behaviour is also what this audience actually experiences.
- **C:** *"Model X performs far better with its recommended prompt format."*
  → Probably true, and listed in Known Limitations. The tradeoff is comparability versus peak performance, and for a comparison index, comparability wins. A "tuned vs untuned" delta is a good v2 study.
- **M:** If a spot-check showed tuning changes the *ranking* rather than the absolute scores, the untuned-only design is no longer sufficient and both conditions get published.

### B5. Refusals and errors excluded from quality, reported as rates

- **D:** Failures get their own taxonomy and rate; they never enter the quality mean.
- **R:** Averaging a refusal in as a zero makes a model that fails 40% of the time look merely mediocre. Reliability and quality are different purchase decisions and must be separately visible.
- **C:** *"You're flattering unreliable models."*
  → The opposite: success rate is published beside every score, and the advisor treats a low success rate as disqualifying for latency-sensitive workloads regardless of quality.
- **M:** Nothing; this is standard practice and the alternative is actively misleading.

### B6. Median of three runs, temperature 0

- **D:** Three runs per case, median score, temp 0 where supported.
- **R:** Free-tier endpoints are nondeterministic even at temp 0 (batching, routing, quantisation vary). One run measures luck. Three is the most repetition the rate limits and the timeline permit.
- **C:** *"n=3 is not enough to characterise variance."*
  → Agreed, and stated. Variance is reported as observed spread, not as a confidence interval, because n=3 doesn't support one. Characterising variance properly is a named v2 goal.
- **M:** If observed spread across three runs regularly exceeds the gaps between models, the whole comparison is underpowered and the design needs more runs and fewer models.

### B7. Rate limits measured empirically, not read from docs

- **D:** Probe real ceilings; report measured vs documented.
- **R:** Documented limits and enforced limits diverge, and the divergence is one of the most useful things this index can publish.
- **C:** *"Isn't probing limits abusive, or a ToS problem?"*
  → It's the single most legally sensitive part of the project and it's handled deliberately: ToS reviewed per provider before any probing, probing done with backoff and stopped at first sustained limit rather than hammered, one account per provider, no circumvention, and results published as measurements rather than as a bypass guide. If a provider's terms forbid publishing benchmarks, that provider is excluded and the exclusion is disclosed.
- **M:** Any provider objection removes that provider from the index immediately.

**Amended 2026-08-13 after the terms review (`ToS-Review.md`).** Probing is now **per-provider, not uniform**. Groq's AUP prohibits use "beyond published parameters, rate limits, or use limitations," which is the plainest description of what deliberate probing does — so **Groq is never actively probed**; its ceiling is published as documented, plus any rejections encountered incidentally during the normal run. Every published ceiling is labelled by how it was obtained: `measured`, `documented`, or `documented + incidental`.

*This is a better design than the original uniform policy, not merely a compliant one. A provider whose terms forbid independent measurement of its own limits is itself information a builder wants, and the label column surfaces it instead of hiding an asymmetry behind a single number.*

---

## Part C — Product decisions

### C1. Static site: published index + client-side advisor

- **D:** One static site — results index plus a browser-side advisor reading a JSON data file. Free hosting.
- **A:** Report only (weaker as product evidence); full app with a backend (doesn't fit 2 weeks at zero budget).
- **R:** Keeps both halves of the story — rigorous measurement *and* a product built on it — while the zero-backend design means no hosting cost, no keys to leak, and no ops burden on a quarterly-refresh product.
- **C:** *"A form over a JSON file isn't really a product."*
  → The product is the judgment encoded in the routing logic and the data underneath it, not the runtime. A backend would add cost and operational risk while changing nothing a user experiences.
- **M:** If feedback shows users want saved comparisons or programmatic access, a JSON API endpoint and shareable URLs come before any backend.

### C2. Quarterly refresh, not a one-off report

- **D:** Ship as a versioned, dated index with a stated refresh cadence.
- **R:** Free-tier terms move constantly. A dated one-off is wrong within months and quietly misleads readers; a cadence turns the project's biggest risk — staleness — into its moat, since maintenance is exactly what nobody else will do.
- **C:** *"Will you actually maintain it?"*
  → The harness is built for re-runs from day one, and every page carries its measurement date so a stale index degrades honestly instead of silently.
- **M:** If refresh cost proves unsustainable solo, cadence drops to semi-annual and is restated publicly rather than quietly missed.

### C3. In-page feedback widget, no accounts

- **D:** Lightweight feedback prompts at decision points, posting to a free form backend. No login, no tracking, no PII.
- **R:** Accounts would kill response rate for a tool used once or twice, and collecting PII on a portfolio project is unjustified risk for no benefit.
- **C:** *"Anonymous feedback is low quality."*
  → For volume signal it's sufficient, and the detailed-disagreement path routes to a public channel where identity is self-selecting. See the UX spec for the instrumentation design.
- **M:** If the dispute channel gets meaningful volume, structured reviewer identity becomes worth adding.

### C4. Full transparency — rubric, test cases, gold answers, judge justifications all published

- **D:** Publish everything, including the raw judgments.
- **A:** Publish results, hold back the test set to prevent gaming.
- **R:** For a solo, unfunded index, auditability *is* the credibility. Nobody is optimising against my test set, and the reproducibility is worth vastly more than the theoretical contamination risk.
- **C:** *"Publishing the set makes it gameable."*
  → A real concern at scale, and the reason each quarterly refresh rotates in a portion of new cases. At v1 scale, the tradeoff is not close.
- **M:** If a vendor visibly optimised against the published set, the set splits into public (methodology demonstration) and held-out (scoring).

### C5. The advisor prices nothing — it publishes volume thresholds and names the cheapest paid path

- **D:** The advisor states the volume at which each free tier's ceiling binds, and — when nothing fits — names which provider's paid tier removes the binding constraint. It states no price, no monthly cost projection, and no currency figure. The reader prices it themselves against the vendor's current page.
- **A:** A hand-maintained price table refreshed quarterly; a live pricing lookup at query time.
- **R:** C1 forbids a backend, so live pricing is impossible — the site is static JSON served from a CDN. A hand-maintained table reintroduces exactly the staleness this project refuses everywhere else: paid pricing moves faster than a quarterly refresh, and a wrong price is worse than no price because the reader acts on it. Volume thresholds are what the benchmark actually measured; prices are what it did not.
- **C:** *"A tool that says 'you'll need to pay' without saying how much isn't finished."*
  → It is finished on the axis it measured. The threshold is the hard part and the part nobody publishes; converting a threshold to a monthly bill is one lookup on a page that is authoritative and current, which this index would never be.
- **M:** If feedback shows readers consistently stall at the paid-path handoff, a dated, clearly-sourced price table with a visible "checked on" stamp becomes worth its maintenance cost — but it ships as a separate, separately-dated surface, never folded into a recommendation.
- **Corrects (2026-08-29):** three documents claimed the opposite and are now amended — `Quality-Cost-Latency-Tradeoff-Framework.md` §8 ("breakeven is computed live from current pricing"), `Model-Selection-Memo.md` §4 ("the advisor computes breakeven from live pricing at query time"), and `UX-and-Feedback-Spec` §3's recommendation card (cost projection in ₹/$ and a paid-tier breakeven callout). `advisor.js` never priced anything; the code was right and the prose drifted. Framework §8 also contradicted itself inside one section, asserting both live pricing and "it does not price anything."

### C6. Up to three ranked survivors per query, with the full filter table beside them

- **D:** A recommendation shows **up to three** surviving models, ranked for the stated workload, the top one carrying its fallback pairing and failover trigger. Every filtered-out model is shown alongside the specific threshold it failed. Fewer than three survivors is a normal outcome, displayed as such — never padded back to three by relaxing a filter.
- **A:** A single winner plus fallback (what `advisor.js` currently returns); a fixed three-result card (what the UX spec promised).
- **R:** Ranking survivors *for a stated workload* is A4 executing, not A4 violated — A4 forbids a query-independent leaderboard precisely because the answer depends on the query, so a query-dependent ordering is the thesis rather than an exception to it. But the filters are hard and often leave one or two survivors (the JSON-output example leaves exactly one after Mistral fails the format floor and Ollama fails latency), so a fixed three is unimplementable. The filter table is the more load-bearing half: it is the evidence that a recommendation is a decision with reasons rather than an opinion, and `advisor.js` already builds it for the none-fit path.
- **C:** *"Three results is a leaderboard with extra steps."*
  → A leaderboard is stable across readers; this ordering changes with every input, and two workloads in the same task routinely invert it. The published index still carries no overall ranking anywhere (A4 stands).
- **M:** If feedback shows the second and third results are ignored, collapse to winner-plus-fallback and keep the filter table — the table is the part that earns its space.

---

## Part D — The three questions most likely to be asked

**"What did you get wrong?"**
Have a real answer ready and update it after the run. Candidates already visible: n=20 per task is thin, and I suspect the adversarial slice at n=3 will produce results I can't stand behind statistically even where they're directionally right. Second: fixing the model set in week one may prove premature if a provider changes its free tier mid-run.

**"What would you do with 10x the budget?"**
Not the frontier models — the free-tier question stays interesting regardless of budget. I'd spend it on n (200 cases per task, not 20), on human scoring across the full set instead of a 20% calibration slice, and on longitudinal re-runs to measure drift, which is the thing nobody tracks and every builder is exposed to.

**"Who would actually use this?"**
Named, in priority order: solo builders pre-revenue, students building portfolio work, and early-stage teams justifying a first spend. The success measure for v1 is not traffic — it's whether anyone reports having changed a model decision because of it. That's the metric the feedback widget is instrumented to capture.

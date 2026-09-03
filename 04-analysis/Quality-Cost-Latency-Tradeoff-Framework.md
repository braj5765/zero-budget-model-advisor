# Quality / Cost / Latency Tradeoff Framework

**2026-08-29 · Braj**

A reusable way to choose a model, derived from building the free-tier index but not specific to it. The framework is what the advisor encodes; the benchmark data is one instantiation of it.

---

## 0. The premise

Most model-selection advice optimises quality and treats cost and latency as constraints to satisfy afterwards. That inverts the real problem. **Cost and latency are product decisions with the same standing as quality**, and the right model is determined by which of the three is binding for a given workload — not by which model is best.

The framework has four steps: **classify the workload → find the binding constraint → filter, don't score → design for failure.**

---

## 1. Classify the workload before comparing anything

Four properties, all of which the *user* knows and no benchmark can:

| Property | Question | Why it decides things |
| :---- | :---- | :---- |
| **Interaction mode** | Is a human waiting? | Splits latency from a preference into a hard filter |
| **Volume** | Requests per day, sustained and peak | Determines whether free tiers are viable at all |
| **Error cost** | What happens when it's wrong? | Sets the quality floor and whether silent failure is tolerable |
| **Output shape** | Prose, a label, or a structure something parses? | Structured output has its own failure mode, unrelated to comprehension |

The fourth is the one usually missed, and the data says it matters most: in this benchmark, a model scoring 82–91 on prose scored **33.8** behind a JSON schema. Comprehension quality does not predict format reliability. A workload description that omits output shape will route to the wrong model.

---

## 2. Find the binding constraint

Exactly one of the three usually binds. Identify it and the decision mostly makes itself.

**Latency binds when a human is waiting.** Interactive work has a threshold, not a gradient — under ~1s feels instant, ~3s is tolerable, beyond that people leave. Above the threshold, extra speed is worth nothing; below it, no amount of quality compensates. This makes latency a **filter first, tiebreak second**, never a weighted score.

**Volume binds when you exceed the tier's ceiling.** Ceilings are step functions, not curves: at 999 requests/day the cost is zero and at 1,001 you are architecting. Also, the ceiling is not always the number the docs emphasise — one provider here caps requests per day, another caps tokens per month, a third has no account-level ceiling that matters because a *shared pool* rejects you based on strangers' traffic. **Find which unit the provider actually meters.**

**Quality binds when errors are expensive.** And "expensive" needs decomposing, because two error types cost differently:
- **Loud failures** — malformed output, refusals, timeouts. Cheap: you detect them and retry.
- **Silent failures** — a fabricated field, an invented causal claim, a confident answer to an unanswerable question. Expensive: they propagate.

A model with a high loud-failure rate and low silent-failure rate is often *safer* than the reverse, even at a lower aggregate score. Aggregate quality metrics obscure this because they average both into one number.

---

## 3. Filter, then rank — never weight into a single score

The standard move is to weight quality, cost and latency into one composite and sort. **Don't.** Composites hide the step functions in §2, and a model that fails your latency threshold is not partially acceptable.

```
1. FILTER  drop anything that fails a hard threshold
           (latency SLA, volume ceiling, output-shape reliability floor)
2. RANK    order survivors on the dimension the workload actually cares about
3. CHECK   verify the winner's ADVERSARIAL sub-score, not just its aggregate
4. PAIR    select a fallback with an uncorrelated failure mode
```

**Step 3 is the one people skip.** Aggregate scores cluster; adversarial scores spread. In this data two models differed by 0.4 points on extraction overall and by 5.5 on the adversarial slice. Aggregate quality describes the happy path. The adversarial sub-score describes the inputs that will actually hurt you, and it is the better predictor of production pain.

---

## 4. Weighting belongs to the user, not the benchmark

Any weighting a benchmark author invents is an unargued assumption about what readers value. This index therefore publishes **unweighted per-dimension scores** and lets the advisor apply weights at query time.

The practical consequence: a benchmark should publish the **most decomposed** numbers it can defend, not the most convenient. Per-dimension, per-difficulty-tier, with `n/a` counts and run-to-run spread attached. Aggregation is a consumer decision. Every level of aggregation destroys information that some reader needed, and the reader can always aggregate — they cannot un-aggregate.

---

## 5. Design for failure, because free tiers fail

Three things a recommendation must include to be complete:

1. **A fallback with an uncorrelated failure mode.** Two providers sharing an upstream pool are one provider. A local model is genuinely uncorrelated with any hosted one — slower, but it does not go down when someone else's traffic spikes.
2. **A failover trigger.** "Fall back on 429" and "fall back after 30 seconds" are different systems. In this data one provider instructed a **1,075-second** backoff; a client obeying it succeeded and a client with a 30-second SLA saw a failure. Same provider, same call, opposite outcomes, depending only on trigger design.
3. **A degradation stance.** When both fail: queue, serve stale, or fail visibly? This is a product decision, not an infrastructure one, and it should be made before it happens rather than during.

---

## 6. Reproducibility is a hidden axis

Free-tier serving is not deterministic even at temperature 0 — measured here at 36–60% identical scores across three identical summarization requests. Batching, routing and quantisation vary invisibly.

Consequences most builders discover the expensive way:
- **Regression tests against a free tier will flap**, and the flapping will be blamed on the application.
- **Cached responses and live responses diverge**, so cache-hit and cache-miss paths behave differently.
- **A/B comparisons need repeats** to separate model differences from run-to-run noise.

**Constrained tasks are markedly more stable than generative ones** — extraction and JSON sat at 79–96% identical while summarization sat at 36–60%. If reproducibility matters, prefer the constrained formulation of your task: ask for a structure rather than prose where you can.

---

## 7. The framework as questions

What the advisor asks, and why each question exists:

| Question | Establishes | Used as |
| :---- | :---- | :---- |
| What are you building? | Task type → applicable dimensions | Selects the score set |
| Is a human waiting? | Latency threshold | **Hard filter** |
| Requests per day? | Volume vs ceiling | **Hard filter** + breakeven |
| What happens when it's wrong? | Quality floor; silent vs loud tolerance | **Ranking modifier** — raises the weight on the adversarial sub-score |
| Prose, label, or structure? | Output shape | **Hard filter** — format reliability is independent of comprehension |
| *(optional)* Which dimensions matter most? | User weighting | Ranking among survivors |

Three hard filters and two ranking inputs. That asymmetry is the framework: **most of model selection is elimination, and only the last step is preference.**

*Corrected 2026-08-29: this table previously listed error cost as a hard filter and claimed four. It is not implemented as one, and should not be — a quality floor would have to be a number invented by the benchmark author, which is exactly what §4 argues against. The one quality-side hard filter that survives (the output-shape floor) is derived from the rubric's own "2 of 3 — usable after a trivial edit" bar rather than chosen to fit the data. Error cost instead shifts ranking weight onto the adversarial sub-score, which is where silent-failure risk is actually visible.*

---

## 8. What this framework does not do

- **It does not produce a best model.** If it did, it would be a leaderboard, and the whole argument here is that leaderboards answer a question nobody has.
- **It does not price anything.** Paid pricing moves faster than any index refreshes, so the framework fixes **volume thresholds** — the point at which a tier's ceiling binds — and names which paid path removes that constraint. Converting a threshold into a monthly bill is the reader's step, against the vendor's current page. *Corrected 2026-08-29: an earlier version of this bullet asserted that "breakeven is computed live from current pricing," contradicting the same bullet's own first sentence and the static, backendless design it describes (Decision C1). See Decision C5.*
- **It does not survive a stale benchmark.** Every filter depends on measurements with a date on them. The framework is durable; the numbers under it are perishable, which is why the index refreshes quarterly and dates every surface.

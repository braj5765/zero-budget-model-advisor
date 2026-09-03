// Zero-Budget Model Advisor -- filter, rank, pair.
//
// Plain ES module. No framework, no build step, no backend (Decision C1).
// Reads its data from 05-site/data/index.json (fetched by the caller and
// passed in -- this module never fetches, so it runs the same in a browser
// or a Node test script without a DOM).
//
// Encodes 04-analysis/Quality-Cost-Latency-Tradeoff-Framework.md S3 exactly:
// FILTER on hard thresholds, then RANK survivors, then CHECK the winner's
// adversarial sub-score, then PAIR a fallback with an uncorrelated failure
// mode. Never a weighted composite across quality/cost/latency (S3: "Don't.
// Composites hide the step functions... a model that fails your latency
// threshold is not partially acceptable").
//
// Output assembly (the twelve-field recommendation shape) lives in
// recommendation.js, imported below -- this file owns filter/rank/pair only.
// Split at 351 lines, past CLAUDE.md's ~300-line refactor trigger, along
// that seam rather than an arbitrary line count.
//
// No overall ranking or best-model figure anywhere (Decision A4) --
// recommend() only ever answers one workload at a time.

import { buildRecommendation } from "./recommendation.js";

// ---------------------------------------------------------------------------
// ROUTING THRESHOLDS -- auditable and adjustable without touching logic below.
// ---------------------------------------------------------------------------

export const THRESHOLDS = {
  // UX-and-Feedback-Spec S3 step 3's three latency options, in ms.
  // "doesnt_matter" has no ceiling -- Infinity always passes the filter.
  latencyMs: {
    doesnt_matter: Infinity,
    interactive: 3000,
    realtime: 1000,
  },

  // Framework S1: "a JSON workload applies a floor on the json-output
  // score." The floor is the rubric's own "2 of 3" bar (Scoring-Rubric.md
  // S2: "Correct in substance, minor flaw. Usable after a trivial edit."),
  // normalised to the 0-100 scale: 2/3 * 100 = 66.7. Set to 65 rather than
  // the exact value so a model landing on the boundary isn't excluded by
  // rounding noise carried through aggregation. This is a rubric-derived
  // threshold, not one picked to fit the four models' actual scores.
  jsonOutputFloor: 65,

  // A survivor below this success rate is not offered as a PRIMARY pick --
  // still eligible as a fallback if nothing else clears the bar, since a
  // documented, high-failure-rate option is still better disclosed than
  // "none of these fit" when it's the only thing available.
  minSuccessRatePctForPrimary: 50,
};

// Requests/day -> tokens/month for a token-metered provider is NOT computed
// here. It is precomputed in 04-analysis/aggregate.py (derive_token_ceiling,
// daysPerMonth=30 stated there) and published in the data as
// tasks[task].benchmark.derived_token_ceiling -- one source of truth,
// inspectable in 05-site/data/index.json without reading this file. This
// module only ever compares the user's requests/day against that published
// figure; it does not re-derive it.

// A local model has no shared upstream with any hosted provider and is the
// clearest available decorrelation (Framework S5 rule 1). If a future
// refresh adds a provider that resells another's inference (as OpenRouter's
// benchmarked model did, sharing a pool with other OpenRouter traffic),
// add it here under the SAME group as whatever it shares infrastructure
// with -- "two providers sharing an upstream pool count as one."
export const CORRELATED_GROUPS = {
  "gemini-3.5-flash-lite": "gemini",
  "groq-llama-3.3-70b": "groq",
  "mistral-small-2603": "mistral",
  "ollama-llama3.2-3b": "local",
};

const LOCAL_MODEL_ID = "ollama-llama3.2-3b";

// Failover trigger is a property of the PRIMARY choice: the condition under
// which a caller should abandon it for the fallback. Framework S5 rule 2:
// "'Fall back on 429' and 'fall back after 30 seconds' are different
// systems" -- so these are concrete, not just "on error".
export const FAILOVER_TRIGGERS = {
  "gemini-3.5-flash-lite":
    "HTTP 429 (measured ceiling 16.6 rpm against a documented 15 rpm), or a " +
    "Retry-After wait longer than your SLA.",
  "groq-llama-3.3-70b":
    "HTTP 429, or an instructed backoff longer than your SLA -- this provider " +
    "sent Retry-After waits up to 1,075s during the benchmark, all eventually " +
    "honoured successfully by a client with no SLA of its own.",
  "mistral-small-2603":
    "HTTP 429 (measured ceiling 52.1 rpm against a documented 60 rpm), or " +
    "approaching the 1B-token/month ceiling -- the binding constraint here is " +
    "tokens, not request count.",
  "ollama-llama3.2-3b":
    "p95 latency longer than your SLA. There is no rate limit to trigger on " +
    "locally; the only failure mode is throughput.",
};

// ---------------------------------------------------------------------------
// Filters -- each returns true/false, never a score. A model failing any
// filter is dropped before ranking, per Framework S3: filter, don't weight.
// ---------------------------------------------------------------------------

function worstP95(entry, tasks) {
  let worst = 0;
  for (const t of tasks) {
    const p95 = entry.tasks[t]?.benchmark?.p95_latency_ms;
    if (p95 == null) return Infinity; // no data for this task -- fails closed
    worst = Math.max(worst, p95);
  }
  return worst;
}

function latencyFits(entry, tasks, latencyNeed) {
  const ceilingMs = THRESHOLDS.latencyMs[latencyNeed];
  if (ceilingMs === Infinity) return true;
  return worstP95(entry, tasks) <= ceilingMs;
}

// Converts a requests/day volume into the tokens/month it would need for
// this model x task, using that model's own measured mean tokens/request
// for the task (tokens_out varies by model even on identical prompts, so
// this is never pooled across models). Returns applies:false when the
// provider has no numeric token ceiling to check against, or no token data
// exists for the task -- in both cases there is nothing to enforce, and
// this is NOT the same as passing: the caller must not treat a missing
// check as a pass on providers that DO have a numeric documented_rpd; this
// function only ever concerns the token axis.
function tokenCeilingInfo(entry, task, requestsPerDay) {
  const derived = entry.tasks[task]?.benchmark?.derived_token_ceiling;
  if (!derived) return { applies: false, fits: true };
  const breakevenReqPerDay = derived.req_per_day_at_token_ceiling;
  return {
    applies: true,
    fits: requestsPerDay <= breakevenReqPerDay,
    breakevenReqPerDay,
    meanTokensPerRequest: derived.mean_tokens_per_request,
    monthlyCeiling: derived.documented_monthly_tokens,
    basis: derived.basis,
  };
}

// Ceilings are metered in different units per provider -- requests/day,
// tokens/month, or (for local) wall clock (Framework S2). A non-numeric
// documented_rpd ("not applicable", "none documented") is never coerced to
// a number and never treated as a numeric zero -- it means there is no
// request-count ceiling, not that the provider is unlimited. Where a
// numeric documented_monthly_tokens exists instead (Mistral), the
// requests/day figure is converted to a tokens/month figure and checked
// against it per task -- this is the fix for "abstaining reads as passing":
// previously a token-metered provider passed every volume check simply
// because it had no request-count ceiling to compare against.
function volumeFits(entry, tasks, requestsPerDay) {
  const rpd = entry.rate_limit_ceiling?.documented_rpd;
  if (typeof rpd === "number" && requestsPerDay > rpd) return false;
  for (const t of tasks) {
    if (!tokenCeilingInfo(entry, t, requestsPerDay).fits) return false;
  }
  return true;
}

function jsonFloorFits(entry, tasks) {
  if (!tasks.includes("json-output")) return true;
  const score = entry.tasks["json-output"]?.task_score;
  return score != null && score >= THRESHOLDS.jsonOutputFloor;
}

function reliabilityFitsForPrimary(entry, tasks) {
  for (const t of tasks) {
    const rate = entry.tasks[t]?.benchmark?.success_rate_pct;
    if (rate != null && rate < THRESHOLDS.minSuccessRatePctForPrimary) return false;
  }
  return true;
}

// ---------------------------------------------------------------------------
// Ranking -- unweighted mean of the workload's dimensions unless the caller
// supplies weights (UX-and-Feedback-Spec S3's collapsed "advanced" sliders).
// Rubric S3: "Task score = unweighted mean of its dimensions... the advisor
// lets the user weight dimensions at query time instead." This is that.
// ---------------------------------------------------------------------------

function taskRankScore(entry, task, dimensionWeights) {
  const taskData = entry.tasks[task];
  if (!dimensionWeights) return taskData.task_score;
  const means = taskData.dimension_means;
  const relevant = Object.keys(means).filter((d) => dimensionWeights[d] != null && means[d] != null);
  if (relevant.length === 0) return taskData.task_score; // no weights apply here
  const totalWeight = relevant.reduce((s, d) => s + dimensionWeights[d], 0);
  return relevant.reduce((s, d) => s + means[d] * dimensionWeights[d], 0) / totalWeight;
}

// errorCost blends in the adversarial sub-score for workloads where silent
// failure is expensive (Framework S7: "what happens when it's wrong ->
// quality floor; hard filter + ranking weight"). Not a new hard filter --
// the specified hard filters are latency, volume and json-output; this is
// the "ranking weight" half of that same table row.
function rankScore(entry, tasks, dimensionWeights, errorCost) {
  const perTask = tasks.map((t) => taskRankScore(entry, t, dimensionWeights));
  const base = perTask.reduce((a, b) => a + b, 0) / perTask.length;
  if (errorCost !== "user_facing_costly") return base;
  const advScores = tasks.map((t) => entry.tasks[t]?.adversarial_sub_score).filter((s) => s != null);
  if (advScores.length === 0) return base;
  const advMean = advScores.reduce((a, b) => a + b, 0) / advScores.length;
  return (base + advMean) / 2;
}

// ---------------------------------------------------------------------------
// Fallback pairing -- prefer the local model when the winner is hosted,
// since it is the clearest uncorrelated failure mode available in this
// dataset (Framework S5 rule 1). Otherwise the next-ranked survivor: every
// scored provider here is independent infrastructure, so "different model"
// already means "different failure domain" among these four.
// ---------------------------------------------------------------------------

function pickFallback(rankedSurvivors, winnerId) {
  const winnerGroup = CORRELATED_GROUPS[winnerId];
  if (winnerGroup !== CORRELATED_GROUPS[LOCAL_MODEL_ID]) {
    const local = rankedSurvivors.find((e) => e.model_id === LOCAL_MODEL_ID);
    if (local) return { model_id: local.model_id, reason: "local -- no shared upstream with any hosted option" };
  }
  const next = rankedSurvivors.find(
    (e) => e.model_id !== winnerId && CORRELATED_GROUPS[e.model_id] !== winnerGroup
  );
  return next ? { model_id: next.model_id, reason: "different provider, independent infrastructure" } : null;
}

// ---------------------------------------------------------------------------
// "None of these fit" -- a valid result (UX-and-Feedback-Spec S3: "Say
// 'none of these fit.' ... A tool that always finds an answer isn't
// advising, it's flattering."). Names the cheapest PATH, not a price
// (Framework S8: "It does not price anything... breakeven is computed live
// from current pricing"): the provider that would have worked here if not
// for the free-tier volume ceiling (request- or token-based, whichever
// binds for it) is the one whose paid tier removes exactly that constraint.
// ---------------------------------------------------------------------------

function cheapestPaidPath(data, tasks, latencyNeed) {
  const candidates = data.scored_models
    .map((id) => ({ model_id: id, entry: data.models[id] }))
    .filter(({ entry }) => jsonFloorFits(entry, tasks) && latencyFits(entry, tasks, latencyNeed));
  if (candidates.length === 0) return null;
  return {
    model_id: candidates[0].model_id,
    note:
      "This provider's free tier is what excluded it here on volume alone -- quality and latency " +
      "already clear your requirements. Its paid tier removes the volume ceiling that bound it " +
      "(request- or token-based); check current pricing at checkout, since this index does not " +
      "track it (Framework S8).",
  };
}

// ---------------------------------------------------------------------------
// recommend() -- the entry point. Pure function: (input, data) -> result.
// Never fetches, never touches the DOM, never ranks across the whole index
// (Decision A4 -- one workload at a time, never an overall best-model).
// ---------------------------------------------------------------------------

export function recommend(input, data) {
  const {
    tasks,
    requestsPerDay,
    latency = "doesnt_matter",
    errorCost = "needs_to_be_right",
    dimensionWeights = null,
  } = input;

  if (!Array.isArray(tasks) || tasks.length === 0) {
    throw new Error("recommend() requires at least one task");
  }

  const allEntries = data.scored_models.map((id) => ({ model_id: id, ...data.models[id] }));

  const filterResults = allEntries.map((entry) => {
    const reasons = [];
    if (!latencyFits(entry, tasks, latency)) {
      reasons.push(`latency: p95 ${worstP95(entry, tasks)}ms exceeds the ${latency} SLA`);
    }
    if (!volumeFits(entry, tasks, requestsPerDay)) {
      const rpd = entry.rate_limit_ceiling.documented_rpd;
      if (typeof rpd === "number" && requestsPerDay > rpd) {
        reasons.push(`volume: ${requestsPerDay}/day exceeds the documented ${rpd}/day ceiling`);
      }
      for (const t of tasks) {
        const tc = tokenCeilingInfo(entry, t, requestsPerDay);
        if (tc.applies && !tc.fits) {
          reasons.push(
            `volume: ${requestsPerDay}/day on ${t} exceeds the derived token-ceiling breakeven of ` +
              `~${Math.round(tc.breakevenReqPerDay).toLocaleString("en-US")} req/day for this task ` +
              `(computed from measured token usage against the documented ` +
              `${tc.monthlyCeiling.toLocaleString("en-US")}/month ceiling -- not a provider-documented figure)`
          );
        }
      }
    }
    if (!jsonFloorFits(entry, tasks)) {
      reasons.push(
        `output shape: json-output score ${entry.tasks["json-output"]?.task_score} is below the ${THRESHOLDS.jsonOutputFloor} floor`
      );
    }
    return { entry, passes: reasons.length === 0, reasons };
  });

  const survivors = filterResults.filter((r) => r.passes).map((r) => r.entry);

  // Always present, win or lose -- "show me the decision table the filters
  // produce" means every model's pass/fail, not just who came out ahead.
  const filterTable = filterResults.map((r) => ({
    model: r.entry.model_id,
    passes: r.passes,
    reasons: r.reasons,
  }));

  if (survivors.length === 0) {
    return {
      fits: false,
      message: "None of the four free-tier models clear your requirements.",
      filters: filterTable,
      cheapest_paid_path: cheapestPaidPath(data, tasks, latency),
      measurement_date: data.judged_at,
    };
  }

  const ranked = [...survivors].sort(
    (a, b) => rankScore(b, tasks, dimensionWeights, errorCost) - rankScore(a, tasks, dimensionWeights, errorCost)
  );

  // Reliability floor: a survivor below it is not offered as the primary
  // pick, but stays available as a fallback candidate (a documented,
  // failure-prone option is still better disclosed than nothing).
  const primaryCandidates = ranked.filter((e) => reliabilityFitsForPrimary(e, tasks));
  const primary = (primaryCandidates.length > 0 ? primaryCandidates : ranked)[0];

  const fallback = pickFallback(ranked, primary.model_id);
  const tokenCeilingByTask = Object.fromEntries(
    tasks.map((t) => [t, tokenCeilingInfo(primary, t, requestsPerDay)])
  );

  return {
    fits: true,
    recommendation: buildRecommendation({
      data,
      entry: primary,
      tasks,
      requestsPerDay,
      latencyNeed: latency,
      worstP95Ms: worstP95(primary, tasks),
      fallback,
      failoverTrigger: FAILOVER_TRIGGERS[primary.model_id],
      tokenCeilingByTask,
    }),
    also_survived: ranked.filter((e) => e.model_id !== primary.model_id).map((e) => e.model_id),
    filters: filterTable,
    measurement_date: data.judged_at,
  };
}

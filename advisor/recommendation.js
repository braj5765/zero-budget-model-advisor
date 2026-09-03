// Zero-Budget Model Advisor -- recommendation output assembly.
//
// Pure output shaping only: given a winner and the context advisor.js
// already computed (fallback choice, failover trigger, per-task token-
// ceiling info), returns the recommendation object the UX-and-Feedback-Spec
// S3 "Recommendation card" needs. No imports from advisor.js -- everything
// this module needs is passed in as arguments, so the dependency runs one
// way (advisor.js -> recommendation.js) and this file can be read, tested
// or reused without pulling in the filter/rank/pair logic that calls it.

export function ceilingSummary(entry) {
  const c = entry.rate_limit_ceiling;
  return {
    documented_rpm: c.documented_rpm,
    documented_rpd: c.documented_rpd,
    documented_monthly_tokens: c.documented_monthly_tokens ?? null,
    provenance: c.provenance,
    note: c.note,
  };
}

// tokenCeilingByTask: { [task]: { applies, fits, breakevenReqPerDay, ... } }
// from advisor.js's tokenCeilingInfo(), one entry per selected task. Only
// tasks where applies===true (a numeric documented_monthly_tokens exists
// for this provider) produce a headroom line -- most models never have one.
export function buildRecommendation({
  data,
  entry,
  tasks,
  requestsPerDay,
  latencyNeed,
  worstP95Ms,
  fallback,
  failoverTrigger,
  tokenCeilingByTask,
}) {
  const taskScores = tasks.map((t) => entry.tasks[t].task_score);
  const advScores = tasks.map((t) => entry.tasks[t].adversarial_sub_score);
  const nNa = tasks.reduce((s, t) => s + entry.tasks[t].n_na_dimension_marks, 0);
  const spreadPct = tasks.map((t) => entry.tasks[t].median_spread.pct_identical_across_runs);
  const successRates = tasks.map((t) => entry.tasks[t].benchmark.success_rate_pct);
  const failureCodes = Object.assign(
    {},
    ...tasks.map((t) => entry.tasks[t].benchmark.failure_code_distribution)
  );

  const rpd = entry.rate_limit_ceiling.documented_rpd;
  const headroomParts = [
    typeof rpd === "number"
      ? `${requestsPerDay}/day against a documented ${rpd}/day ceiling`
      : `${requestsPerDay}/day -- no documented daily-request ceiling for this provider`,
  ];
  for (const t of tasks) {
    const tc = tokenCeilingByTask[t];
    if (tc && tc.applies) {
      headroomParts.push(
        `derived token ceiling ~${Math.round(tc.breakevenReqPerDay).toLocaleString("en-US")} req/day for ${t} ` +
          `-- computed from measured token usage, NOT a provider-documented figure, and differs per ` +
          `task because prompt and response lengths vary`
      );
    }
  }

  return {
    model: entry.model_id,
    verdict:
      `Quality ${taskScores.map((s) => s.toFixed(1)).join("/")} on ${tasks.join(", ")}, ` +
      `p95 ${worstP95Ms}ms, ${headroomParts[0]}.`,
    fit: {
      quality: taskScores,
      latency_ms: worstP95Ms,
      latency_need: latencyNeed,
      headroom: headroomParts.join("; "),
    },
    adversarial_sub_score: advScores,
    n_na_dimension_marks: nNa,
    run_to_run_spread_pct_identical: spreadPct,
    measured_p95_ms: worstP95Ms,
    rate_limit_ceiling: ceilingSummary(entry),
    success_rate_pct: successRates,
    failure_code_distribution: failureCodes,
    measurement_date: data.judged_at,
    judge_model: data.judge_model,
    judge_prompt_version: data.judge_prompt_version,
    fallback: fallback && {
      model: fallback.model_id,
      reason: fallback.reason,
      failover_trigger: failoverTrigger,
    },
  };
}

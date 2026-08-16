# Harness Spec — Zero-Budget Model Advisor

**v1.0 · 2026-08-10 · Owner: Braj**

The harness collects the raw material the rubric scores. It does **not** score, judge, or analyse — those live downstream in `/scoring` and `/analysis`. Dependencies point one way (`harness → scoring → analysis → site`); the harness must not import from any of them.

Written before the code so the record format is settled while it's still cheap to change. The expensive version of this mistake is finishing ~1,500 calls and discovering a field you need at analysis time was never captured.

---

## 1. What it does

Five jobs, in order of importance:

1. **Execute the run matrix** — every test case against every model, three times.
2. **Record one complete row per call** — nothing derived, nothing discarded.
3. **Survive rate limits** — back off, wait, resume; never lose completed work.
4. **Resume after interruption** — a crash at call 1,200 resumes at 1,201, not 1.
5. **Probe real rate-limit ceilings** — a separate mode, run independently of the main benchmark.

**Run matrix:** 100 cases × 5 models × 3 runs ≈ **1,500 calls**. Sequenced per provider, not parallel — parallelism against a free tier just buys you 429s faster.

---

## 2. The call record — the load-bearing part

One JSON object per call, appended to a dated JSONL file in `/results`. Every field below is captured on **every** call, including failed ones.

### Identity
| Field | Why it's here |
| :---- | :---- |
| `call_id` | Unique; makes any single result traceable back to its raw row |
| `case_id` | Links to the test case in `/data` |
| `task` | One of the five tasks |
| `difficulty` | typical / hard / adversarial — needed for the adversarial sub-score |
| `model_id`, `provider` | — |
| `model_version` | Free tiers silently swap model versions; without this, a cross-quarter comparison is meaningless |
| `run_index` | 1–3, for the median-of-three rule |

### Request
| Field | Why it's here |
| :---- | :---- |
| `prompt`, `system_prompt` | Full text stored, not a hash — reproducibility requires the actual input |
| `temperature`, `max_tokens`, other params | Proof that conditions were identical across models |
| `timestamp_utc` | Every result is a point-in-time reading |

### Response
| Field | Why it's here |
| :---- | :---- |
| `response_text` | Raw and unmodified. **No trimming, no stripping of markdown fences** — fence-wrapping is itself a JSON parseability failure and must survive to scoring |
| `finish_reason` | Distinguishes a truncation from a short answer |
| `tokens_in`, `tokens_out` | **Required for cost projection and breakeven.** If the provider doesn't return them, estimate and set `tokens_estimated: true` |
| `http_status` | — |

### Timing
| Field | Why it's here |
| :---- | :---- |
| `latency_ms` | Wall clock, request sent → response complete |
| `time_to_first_token_ms` | Where streaming is available; it's the number that actually matters for interactive UX |
| `queue_wait_ms` | Time spent in harness-side backoff before the request went out. **Kept separate from `latency_ms`** — folding backoff into latency would make a rate-limited model look slow rather than limited, and those are different problems with different fixes |

### Outcome
| Field | Why it's here |
| :---- | :---- |
| `status` | `success` or `failure` |
| `failure_code` | One of the eight codes in rubric §6 |
| `error_raw` | Provider's own message, verbatim — the source material for the failure-mode writeup |
| `retry_count` | How many attempts this call took before succeeding or being abandoned |

### Run context
`run_id`, `harness_version`, `git_commit` — so any row can be tied to the exact code that produced it.

**Rule: the harness never overwrites.** Each run appends to a new dated file. Re-running a case writes a new row; it does not replace the old one.

---

## 3. Rate-limit and failure handling

Per CLAUDE.md rule 3, retry logic lives **inside each model client** and nowhere else. The runner sees only `success` or `failure` and never contains provider-specific branching.

**Backoff policy:**

- `429` / quota errors → exponential backoff (2s, 4s, 8s, 16s, 32s), honouring `Retry-After` when the provider sends one. Max 5 attempts, then log `RATE_LIMIT` and move on.
- `5xx` → up to 3 retries, then log `API_ERROR`.
- Timeout → **no retry.** Log `TIMEOUT` and move on; a timeout is a result, not an accident.
- Refusal, empty, malformed → **never retried.** These are the findings. Retrying until the model complies would erase the exact behaviour the benchmark exists to measure.

That last line is the one to get right. Retrying a refusal is the single easiest way to accidentally launder a model's failure rate into a clean-looking score.

**Provider pacing:** each client declares a minimum inter-request delay from config, applied unconditionally. Cheaper to run slightly slow than to trip abuse detection and lose an account mid-run.

---

## 4. Resumability

Before each call, the runner checks whether `(case_id, model_id, run_index)` already exists in the current run's output. If it does, skip.

This makes the run **idempotent and interruptible**: re-running the command after a crash, an account lockout, or an overnight stop picks up exactly where it stopped. With ~1,500 calls against free tiers spread over days, interruption is the expected case, not the exception.

**Run identity — clarified 2026-08-13.** §2 says each run appends to a new dated file; §4 says resumption checks "the current run's output." Read together these were ambiguous, and a date-derived default resolves them wrongly: **a run spanning midnight would start a second file and silently re-execute every completed call**, burning the scarcest resource in the project. Since a 1,500-call run across rate-limited free tiers is *expected* to span days, that is the normal case, not an edge case.

**A run is identified by its `run_id`, not by the calendar.** Resolution order:

1. `--run-id X` given → use it.
2. `--new-run` given → create a fresh id (date, disambiguated if one already exists).
3. Neither → **resume the most recent existing run file.** Starting fresh is the explicit action; resuming is the default, because the cost of a wrong resume is one duplicate-suppressed call and the cost of a wrong fresh start is ~1,500 wasted calls.

On startup the runner prints the resolved `run_id`, the count already complete, and the count remaining. Silent resumption of the wrong run is the failure this line exists to prevent.

---

## 5. Rate-limit probing mode

A separate command, run **after** the main benchmark — never before, and never concurrently. It measures the ceiling the docs don't tell you.

**Scheduling — clarified 2026-08-13.** Probing runs after the benchmark *and after quota has recovered*, i.e. on a later day. The prober skips any provider with a `RATE_LIMIT` row in the last 24 hours, which is both ToS-conservative and methodologically necessary: a ceiling measured against a partly-exhausted quota is a measurement of the benchmark's leftovers, not of the tier. Run the benchmark and the probe on separate days, or every provider will be skipped and no ceiling will ever be measured.

**Retries are disabled during probing.** With the standard policy active, a 429 triggers up to five backoff-and-retry attempts — meaning the prober would keep requesting for ~60 seconds *after* being told no, and would record the exhaustion point rather than the first rejection. Disabling retries is simultaneously more accurate and more conservative. The effective retry setting is recorded on every probe row so a reader can tell which policy produced the number.

- Sends a fixed trivial prompt at a slowly increasing rate.
- Stops at the **first sustained limit** (2 consecutive rejections), then stops entirely. Does not hammer, does not attempt to characterise the recovery curve, does not probe again for 24 hours.
- Records: requests before first rejection, requests-per-minute at rejection, error message, whether the limit appears to be per-minute / per-day / token-based, and the wall-clock time to recovery.
- Output: **measured ceiling vs documented ceiling** — one of the more useful things this index will publish.

**Constraints, non-negotiable:** provider ToS reviewed and recorded before probing. One account per provider. No key rotation, no IP rotation, no circumvention of any kind. If a provider's terms prohibit benchmarking or publishing results, that provider is dropped from the index and the exclusion is disclosed. See Decision Log B7.

---

## 6. Structure

```
/harness
  config.yaml        models, limits, timeouts, pacing, paths — the only file that changes to add a provider
  runner.py          matrix execution, resumability, record writing
  clients/           one thin client per provider
  probe.py           rate-limit probing mode
```

**The one abstraction justified up front** (per CLAUDE.md rule 2, which otherwise forbids abstracting before the third occurrence): a shared client interface, because there are five implementations on day one.

```
call(prompt, system_prompt, params) -> CallResult
```

`CallResult` carries the response fields, timing, and outcome. Every provider quirk — auth, payload shape, error format, backoff, token accounting — is absorbed inside its client. **Nothing provider-specific may appear in `runner.py`.** If it does, the abstraction has failed and should be fixed rather than worked around.

Adding a sixth provider next quarter = one new client + a config entry. No change to the runner.

---

## 7. Definition of done

- All ~1,500 rows present in `/results`, or accounted for by a logged failure code.
- Zero rows missing `tokens_in`/`tokens_out` without `tokens_estimated: true`.
- A killed and restarted run produces no duplicate `(case_id, model_id, run_index)`.
- `runner.py` contains no provider names.
- Measured-vs-documented rate limits recorded for all five providers.

---

## 8. Explicitly out of scope for v1

Parallel execution, a live dashboard, automatic scheduling of the quarterly refresh, streaming-response reconstruction beyond time-to-first-token, and any retry logic outside the clients. Each is a v2 candidate; none is needed to produce a defensible dataset.

---

## Changelog

| Version | Date | Change |
| :---- | :---- | :---- |
| 1.0 | 2026-08-10 | Initial spec, pre-implementation |

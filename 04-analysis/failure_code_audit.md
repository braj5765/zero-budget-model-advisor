# RATE_LIMIT `error_raw` audit

**Source:** `03-results/run-2026-08-15T114622Z.jsonl` (the benchmark run, 1,500 rows). Required per `PROJECT-STATE.md` §4b.4 before any failure-rate table is published: the harness matched `"quota"` loosely on purpose when assigning `RATE_LIMIT` at record time, deferring the real classification to here, where the actual provider strings can be read.

**Method:** read every non-`success` row's `error_raw`, parsed as JSON, and grouped by provider on the distinguishing fields (`http_status`, `error.message`, `error.metadata.limit_source`, `error.metadata.provider_name`).

---

## Scope of the failures

**Only one provider produced any failure in the benchmark run.** Gemini, Groq, Mistral and Ollama — the four scored models — are each 300/300 `success`. This matches the 2026-08-16 finding already on record (`PROJECT-STATE.md` §8) and is reconfirmed here directly from the raw file, not assumed:

| Provider | Failure rows | Failure code (as recorded) |
| :---- | :---- | :---- |
| gemini | 0 | — |
| groq | 0 | — |
| mistral | 0 | — |
| ollama | 0 | — |
| **openrouter** | **204** | `RATE_LIMIT` |

OpenRouter is not scored on quality (Decision A5) — these 204 rows have no bearing on any of the four models' failure-rate or quality tables. They matter only for OpenRouter's own entry in the failure-rate and rate-limit tables, which — per this session's instruction — is still published even though OpenRouter is excluded from quality scoring.

## Observed strings, OpenRouter's 204 failure rows

Every one of the 204 rows is **byte-identical in structure**:

- `http_status`: `429` — 204/204
- `error.message`: `"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day"` — 204/204
- `error.metadata.limit_source`: `"openrouter_free_tier_daily"` — 204/204
- `error.metadata.provider_name`: `null` — 204/204 (this is the account-level daily cap, not an upstream-provider-specific rejection — `provider_name` is only populated for the shared-pool kind of 429, seen previously during rate-limit probing but not present anywhere in this benchmark run)
- 0 rows had an unparseable `error_raw`

**No distinct strings beyond this one pattern were observed.** There is nothing to disambiguate — every row already carries an explicit, unambiguous `limit_source` naming exactly which cap was hit.

## Reclassification

**None required.** The loose `"quota"` match the harness used at record time happens to be correct on every one of the 204 rows: all 204 are genuinely `RATE_LIMIT` rejections against OpenRouter's documented `free-models-per-day` cap, evidenced by the provider's own 429 body, not inferred. This is the same daily-cap behaviour already characterized in Decision A5 and the 2026-08-16 correction (successes per calendar day, 47 and 49, matched the documented 50/day almost exactly) — this audit adds the row-by-row evidence trail behind that characterization rather than changing it.

**Distinct from the shared-pool finding.** `PROJECT-STATE.md`'s 2026-08-17 entry documents a *second*, different OpenRouter ceiling — `upstream_provider_shared_pool`, with a populated `provider_name` (`Darkbloom`) — observed during rate-limit *probing* (`probe.jsonl`), not in the benchmark run. That finding stands; it simply isn't present in `run-2026-08-15T114622Z.jsonl`'s 204 rows, which are uniformly the daily-cap kind. Both ceilings are real and both belong in OpenRouter's published profile, from their respective sources.

## Conclusion

The failure-rate table may now be published for OpenRouter using the existing `RATE_LIMIT` code as-is: **204/300 attempts (68.0%) failed, all confirmed genuine daily-cap rejections**, 96/300 (32.0%) succeeded. No row needs recoding, no row is ambiguous, and no row's `error_raw` was unparseable.

---

# `probe.jsonl` provisional-row audit

**Source:** `03-results/probe.jsonl`, 6 rows. Required before any rate-limit ceiling is published (`PROJECT-STATE.md` §4b.4): only 3 of the 6 rows carry the `ceiling_reached` key at all, and the 3 that don't predate the honest-recording fix (`probe.py`, commit `1e898e6`, 2026-08-17).

**Rule applied:** take the **latest row per `model_id`**; treat a missing `ceiling_reached` as untrustworthy and never as a measured ceiling.

| `model_id` | Row (date, `git_commit`) | `ceiling_reached`? | Used? |
| :---- | :---- | :---- | :---- |
| `gemini-3.5-flash-lite` | 2026-08-16, `6b1446b` | absent | **No** — superseded |
| `gemini-3.5-flash-lite` | 2026-08-17, `1e898e6` | `true` | **Yes** — latest, trustworthy |
| `mistral-small-2603` | 2026-08-16, `6b1446b` | absent | **No** — superseded |
| `mistral-small-2603` | 2026-08-17, `1e898e6` | `true` | **Yes** — latest, trustworthy |
| `openrouter-gpt-oss-20b` | 2026-08-16, `6b1446b` | absent | **No** — superseded |
| `openrouter-gpt-oss-20b` | 2026-08-17, `1e898e6` | `true` | **Yes** — latest, trustworthy |

**What was wrong with the three superseded rows, concretely:** the Gemini and Mistral 2026-08-16 rows both record `requests_before_first_rejection: 200` with an **empty `error_raw`** — no rejection actually happened; the probe hit a hardcoded 200-request backstop and stopped, and the pre-fix code recorded that stop as if it were a measured rejection point. That number (200) never reflects a real provider ceiling for either model and **must not reach any published figure** — not as a ceiling, not as a footnote comparison. The OpenRouter 2026-08-16 row is different in kind — it did hit a real, documented rejection (`requests_before_first_rejection: 1`, populated `error_raw`, daily-cap message) — but it is still superseded by the 2026-08-17 row per the stated rule (latest wins), and the two rows measure different things regardless (daily cap vs. shared-pool), so using the latest is also the more informative choice, not just the ruleful one.

**Ceilings used for the published table** (from the 3 retained, `ceiling_reached: true` rows, plus non-probed providers per standing policy):

| Model | Measured ceiling | Documented | Provenance | Source |
| :---- | :---- | :---- | :---- | :---- |
| `gemini-3.5-flash-lite` | 16.6 rpm at rejection (39 requests in) | 15 rpm | `measured` | `probe.jsonl`, confirmed by Gemini's own 429 body (`limit: 15`, `generate_content_free_tier_requests`) |
| `mistral-small-2603` | 52.1 rpm at rejection (96 requests in) | 60 rpm | `measured` | `probe.jsonl`; bare error prose, `limit_period_guess: unknown` — not guessed beyond what the string supports |
| `groq-llama-3.3-70b` | not probed (ToS-Review R-1: AUP forbids testing beyond published limits) | 30 rpm / 1,000 rpd | `documented + incidental` | Not in `probe.jsonl`. Incidental evidence from the benchmark run itself: 7 rows show `retry_count > 0` (8 retries total, one row retried twice), backoff waits up to **1,075s**, all eventually succeeding under the harness's own retry policy — real contention was encountered and absorbed, never failed |
| `openrouter-gpt-oss-20b` | **two distinct ceilings, both real, both published**: (a) daily cap, 50/day documented, 204/300 benchmark-run rejections confirm it empirically; (b) shared-pool, 24.1 rpm at rejection (2 requests in), `limit_source: upstream_provider_shared_pool`, `provider_name: Darkbloom` | 20 rpm / 50 rpd | `measured` (both) | `probe.jsonl` row 5 for (b); benchmark run + `probe.jsonl` row 2 (superseded but corroborating) for (a) |
| `ollama-llama3.2-3b` | not applicable — local, no network service, no rate limit exists to measure | — | `documented` (n/a) | `config.toml`: "local — no service terms" |

This table, not the raw `probe.jsonl` rows, is what the aggregation output cites.


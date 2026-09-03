# Scores summary — 2026-08-29

Rubric v1.7. Judge `minimax/minimax-m3:free` (GMICloud), prompt v1.3, judged 2026-08-29.

No overall ranking or best-model figure is computed here (Decision A4). OpenRouter is excluded from quality scoring (Decision A5) and appears only in the failure-rate and rate-limit sections below.

## gemini-3.5-flash-lite

| Task | Score | Adversarial | n/a | Median identical | Success | p95 latency | Failures |
| :---- | ---: | ---: | ---: | ---: | ---: | ---: | :---- |
| classification | 93.3 | 92.6 | 1 | 93.2% | 100.0% | 4515ms | — |
| extraction | 92.1 | 72.2 | 0 | 81.2% | 100.0% | 1577ms | — |
| json-output | 67.1 | 66.7 | 18 | 79.0% | 100.0% | 1828ms | — |
| rag-qa | 96.2 | 97.2 | 0 | 90.0% | 100.0% | 2125ms | — |
| summarization | 88.3 | 77.8 | 0 | 58.8% | 100.0% | 2764ms | — |

Rate-limit ceiling: documented 15 rpm / 1000 rpd, provenance **measured**. Confirmed by Gemini's own 429 body (limit: 15, generate_content_free_tier_requests).

## groq-llama-3.3-70b

| Task | Score | Adversarial | n/a | Median identical | Success | p95 latency | Failures |
| :---- | ---: | ---: | ---: | ---: | ---: | ---: | :---- |
| classification | 85.6 | 88.9 | 1 | 81.4% | 100.0% | 579ms | — |
| extraction | 92.5 | 66.7 | 0 | 86.2% | 100.0% | 1389ms | — |
| json-output | 87.5 | 63.9 | 6 | 95.9% | 100.0% | 1797ms | — |
| rag-qa | 96.7 | 97.2 | 0 | 93.8% | 100.0% | 577ms | — |
| summarization | 75.4 | 58.3 | 0 | 36.2% | 100.0% | 985ms | — |

Rate-limit ceiling: documented 30 rpm / 1000 rpd, provenance **documented + incidental**. Never actively probed (AUP, ToS-Review R-1). Incidental evidence from the benchmark run: 8 retries across 7 rows, backoff waits up to 1075s, all eventually succeeded under the harness's own retry policy.

## mistral-small-2603

| Task | Score | Adversarial | n/a | Median identical | Success | p95 latency | Failures |
| :---- | ---: | ---: | ---: | ---: | ---: | ---: | :---- |
| classification | 84.4 | 81.5 | 1 | 96.6% | 100.0% | 889ms | — |
| extraction | 90.8 | 75.0 | 0 | 86.2% | 100.0% | 3171ms | — |
| json-output | 33.8 | 33.3 | 39 | 92.7% | 100.0% | 2264ms | — |
| rag-qa | 85.4 | 77.8 | 0 | 86.2% | 100.0% | 1327ms | — |
| summarization | 82.5 | 75.0 | 0 | 60.0% | 100.0% | 2375ms | — |

Rate-limit ceiling: documented 60 rpm / none documented rpd / 1,000,000,000 tokens/month, provenance **measured**. Bare error prose; limit_period_guess left 'unknown', not guessed beyond the string. The binding ceiling here is token-based (documented_monthly_tokens), not request-based.

**Derived token-ceiling req/day equivalent — computed from measured token usage, NOT a provider-documented figure, differs per task:**
  - classification: ~168,947 req/day (mean 197.3 tokens/request measured)
  - extraction: ~65,198 req/day (mean 511.3 tokens/request measured)
  - json-output: ~129,862 req/day (mean 256.7 tokens/request measured)
  - rag-qa: ~115,241 req/day (mean 289.2 tokens/request measured)
  - summarization: ~94,438 req/day (mean 353.0 tokens/request measured)

## ollama-llama3.2-3b

| Task | Score | Adversarial | n/a | Median identical | Success | p95 latency | Failures |
| :---- | ---: | ---: | ---: | ---: | ---: | ---: | :---- |
| classification | 57.8 | 66.7 | 1 | 83.1% | 100.0% | 22172ms | — |
| extraction | 72.9 | 44.4 | 0 | 67.5% | 100.0% | 81703ms | — |
| json-output | 75.8 | 55.6 | 9 | 91.5% | 100.0% | 60859ms | — |
| rag-qa | 71.7 | 58.3 | 0 | 76.2% | 100.0% | 17359ms | — |
| summarization | 72.1 | 77.8 | 0 | 45.0% | 100.0% | 39265ms | — |

Rate-limit ceiling: not applicable, provenance **documented (not applicable)**. Local, no network service, no rate limit exists to measure.

## openrouter-gpt-oss-20b — excluded from quality scoring, failure-rate/ceiling only

Overall: 96/300 succeeded (32.0%), failures: {'RATE_LIMIT': 204}.

Rate-limit ceiling: documented 20 rpm / 50 rpd, provenance **measured**. Two distinct, real ceilings -- an account-level daily cap and a shared-pool ceiling unrelated to the account's own quota. Both published.

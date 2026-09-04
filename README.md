# Zero-Budget Model Advisor

An original benchmark of free-tier LLMs (Gemini, Groq, Mistral, and a local Ollama model) across five everyday builder tasks — summarization, extraction, classification, RAG Q&A, structured JSON output — plus a client-side advisor that routes a stated workload to the model that actually fits it, unpriced and filter-first.

**Live site:** https://braj5765.github.io/zero-budget-model-advisor/

## Headline finding

The zero-budget constraint is the thesis: nobody has rigorously published what you can actually ship on a free tier. This index measures it directly across 1,500 benchmark calls and 1,200 judged responses, publishes no overall leaderboard (the right model depends on your volume, latency need, and error tolerance), and instead ships a routing advisor that filters and ranks against the workload you actually have.

## The judge is uncalibrated — stated plainly, not buried

The LLM judge behind every score here cleared its calibration gate in-sample (κ=0.650) but failed to generalize: held-out agreement measured **κ=0.358**, below this project's own pre-registered 0.45 floor. That gate is published as failed, not quietly re-run until it passed. The full account — what caused it, what was adjudicated, what stays structurally unfixable at this scale, and what the next quarterly refresh actually fixes — is in [`04-analysis/Known-Limitations.md`](04-analysis/Known-Limitations.md), and it's linked from every page of the live site, not just this README.

## Start here

[`00-planning/PROJECT-STATE.md`](00-planning/PROJECT-STATE.md) is the entry point for this repo — where the project stands, what's decided and closed, and what's still open. Its §8 session log is the dated, unedited record of how the work actually proceeded, including the reversals and the failed gate.

Everything is published: the rubric, the test cases, the gold references, the judge's justifications, and the raw benchmark rows in `03-results/`. If you think a score is wrong, `/results` on the live site has a dispute form on every cell.

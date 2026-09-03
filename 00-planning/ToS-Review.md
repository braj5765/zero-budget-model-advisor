# Provider Terms Review

**Reviewed 2026-08-13 · Source: `API Providers T&C.txt` (Gemini, Groq, OpenRouter, Mistral) · Reviewer: Braj**

Closes open question 2. Scope of the review: (a) does benchmarking violate the terms, (b) may results be published, (c) is empirical rate-limit probing permitted, (d) does anything break the zero-budget constraint.

**This is a good-faith reading of the terms as written, not legal advice.** Where a term is ambiguous, the conservative reading is taken.

---

## Summary

| Provider | Benchmark permitted | Publish results | Empirical limit probing | Zero-budget safe |
| :---- | :---- | :---- | :---- | :---- |
| Gemini | Yes | Yes | Cautious — no explicit bar | Yes |
| Groq | Yes | Yes | **No — do not probe** | Yes |
| OpenRouter | Yes, with conditions | Yes | Cautious | **Yes — verified on zero balance, see O-1** |
| Mistral | Yes | Yes | Cautious — policy is content-only | Yes |

**No provider prohibits benchmarking or publishing comparative results.** The project's core premise survives the review. Four findings do change how it's executed.

---

## Findings that change the project

### G-1 · Gemini trains on free-tier input, which contaminates future refreshes

Gemini's Unpaid Services terms: *"Google uses the content you submit to the Services and any generated responses to provide, improve, and develop Google products and services and machine learning technologies"*, and human reviewers may read and annotate it.

Not a compliance problem — it is a **methodology problem**. Test cases submitted to the free tier may enter training data, so by a later quarterly refresh, Gemini could be scoring partly on memorisation. This is exactly the contamination the original-authorship policy was designed to prevent, arriving through a different door.

**Actions:**
- Case rotation moves from advisory to required: **≥25% of cases replaced each refresh**, and the rotated-in cases are never published before they are used.
- Every published result records which providers train on submitted input, as a stated limitation.
- Also confirms an existing decision: submitting only original, non-sensitive text satisfies Gemini's *"do not submit sensitive, confidential, or personal information to the Unpaid Services"* instruction. No change needed, but the reasoning is now on the record.

### R-1 · Groq's AUP forbids the rate-limit probing method

Groq's Acceptable Use Policy prohibits use *"beyond published parameters, rate limits, or use limitations"* and use *"in a manner that burdens, disables, impairs, or interferes with the Cloud Services."*

Deliberately increasing request rate until rejection is the plainest reading of what that clause exists to stop. The conservative reading governs.

**Action — probing policy is now per-provider, not uniform:**
- **Groq: no active probing.** Publish the documented limit, plus any rate-limit rejections encountered incidentally during the normal benchmark run. Label it `documented + incidental`.
- **Others:** probing remains permitted but stays conservative — stop at first sustained limit, no repeat within 24 hours.
- Every published ceiling is labelled with **how it was obtained** (`measured`, `documented`, or `documented + incidental`). This is more honest than a uniform column anyway, and the asymmetry is itself a publishable finding: a provider whose terms forbid measuring its own limits is information a builder wants.

### O-1 · OpenRouter credit requirement — RESOLVED 2026-08-13, OpenRouter stays in

**Verified empirically:** a `:free` model returned a successful completion on a zero credit balance. OpenRouter remains in the benchmark; no money spent.

**Publish this.** The terms say credits are required to make API calls; in practice free models are callable without purchase. That gap between documented and actual behaviour is precisely the kind of thing this index exists to surface, and it belongs in the OpenRouter model profile — a builder reading only the terms would wrongly conclude the free tier is unusable at zero budget.

**Standing risk:** this is undocumented behaviour, not a contractual guarantee, so it can be withdrawn without notice. Re-verify at every quarterly refresh before assuming OpenRouter is still zero-budget viable.

*Original finding retained below for the record.*

---

### O-1 (original) · OpenRouter may require a credit purchase — a live threat to zero budget

OpenRouter's terms state: *"Currently, OpenRouter requires users to purchase Credits to make API calls and access the Service,"* minimum $5.

If free models cannot be called on a zero balance, **OpenRouter cannot be in this benchmark.** The zero-budget constraint is the thesis; spending $5 to test it would invalidate the premise, not bend it.

**Action — verify before writing the OpenRouter client.** Create the account, attempt one call to a free model with a zero balance.
- Works → include, and note in the methodology that free models are callable without purchase despite the terms' general statement.
- Fails → **drop OpenRouter and disclose the exclusion and its reason.** Do not substitute a paid call.

This is the highest-priority open item; it can change the model set.

### O-2 · "Adversarial" cases are not Red Teaming, and the methodology must say so

OpenRouter §8 prohibits Red Teaming without written approval, defining it as *"prompt injection, jailbreaking, or taking any other adversarial action designed to compromise any Models and/or violate any Model Terms."*

The benchmark's adversarial cases do none of that. They are ordinary, benign inputs designed to reveal *unforced* failures — invented causation, fabricated precision, over-confident answers on unanswerable questions. No safety measure is bypassed, no policy-violating output is sought, no model is compromised.

**Action:** state this distinction explicitly in the published methodology. Consider labelling them **"robustness cases"** in public materials while keeping `adversarial` as the internal `difficulty` value — the word invites exactly the wrong reading from someone skimming for a terms violation.

---

## §5.1 model-terms flow-down · Judge model — 2026-08-28

**Trigger:** `qwen2.5:7b` failed the calibration κ gate twice (JUDGE-RUN-PLAN.md §4b) and `14b` isn't runnable on this machine. The local-judge route is closed. Per §4b's resolved escalation path, a hosted free judge outside the benchmark set is next — OpenRouter is eligible for this specific role because it was cut from scoring (Decision A5), so no model it serves is under test and the self-preference concern (Decision B3) does not arise for the judge itself. This closes the flow-down action item deferred at line 88 above: *"If OpenRouter survives O-1, record which specific free models are used and confirm each one's terms."*

**Candidate selection.** Queried `https://openrouter.ai/api/v1/models` directly (21 free models currently listed; a first pass via a summarizing fetch tool under-reported this to 7 and is not trusted — the raw JSON was pulled and filtered in Python instead). Screened against three criteria: substantially more capable than a 7B, no lineage or provider overlap with any benchmarked model, callable at zero balance.

Disqualified: `openrouter/free` (an auto-router, not a pinned model — fails rubric §5's per-index judge-version pinning outright); Google Lyria variants (audio, wrong modality); Liquid LFM-2.6B, Poolside, Cohere north-mini, dots-studio, Nemotron-lightning/content-safety/nano (too small or domain-specific for a 4-dimension judgment task); **`nvidia/nemotron-3-ultra-550b-a55b:free`** — verified via web search to be built on **Llama 4** (formally released as Llama-4-Nemotron-Ultra-550B), which the second criterion explicitly rules out given two benchmarked models (Groq, Ollama) are themselves Llama variants.

**Pick: `z-ai/glm-5.2:free`** (Zhipu AI / Z.ai, MIT-licensed, 753B parameters, 1M native context). Independent architecture and organisation — no relation to Google (Gemini), Meta (Llama, via Groq or Ollama), or Mistral AI. Reported strength is specifically in careful multi-step, rule-following reasoning (SWE-bench Pro, agentic/coding indices) — the same class of task the 7B failed on (conditional-branch application, literal-token reading), which is why it's proposed over the similarly-clean but smaller `minimax/minimax-m3:free` (428B, weaker reported reasoning index).

**Upstream serving provider — checked, not assumed.** OpenRouter's per-model endpoint listing (`/api/v1/models/z-ai/glm-5.2:free/endpoints`) shows the free route is served by exactly **one** provider, **Decart** (`decart/fp4`, fp4-quantized, 256K context — not Z.ai's own infrastructure, and not any of the 37 paid resellers listed for the metered `z-ai/glm-5.2` slug, one of which is coincidentally Mistral's own cloud — irrelevant to self-preference since that's an infrastructure-hosting relationship for someone else's weights, not Mistral's model judging itself). Both Z.ai's and Decart's terms apply.

**Z.ai terms (`chat.z.ai/legal-agreement/terms-of-service`):** *"use of the Z.ai's models, prompts, or model-generated content for the development, training, labeling, fine-tuning, optimization... of external models is strictly prohibited"*; also bars using the service to *"develop, train, or enhance algorithms, models, or technologies that directly or indirectly compete."* Standard train-a-competitor clause. **Reading:** scoring already-generated, static responses from the four benchmarked models for a published index does not develop, train, label, fine-tune, or optimise any of them — nothing about those models changes as a result of being judged. This is the same class of distinction as O-2 (adversarial cases are not Red Teaming): the clause's plain target is model distillation, not evaluation. Flagged rather than waved through because "labeling" sits closest to our actual use (assigning a 0–3 score is, literally, labeling a response) — the conservative reading this file commits to elsewhere would pause here if the labels fed back into training any of the four scored models, which they do not; they only feed a published comparison. Automated API access is not separately restricted — the anti-bot clause (*"deep linking, page scraping, social bots, spiders... to access this service"*) reads, like OpenRouter's own equivalent clause, as aimed at the web app, not the API. Input-use-for-training: *"we will not use your User Content for developing or improving Services, unless you explicitly agree"* for API users specifically — cleaner than Gemini's G-1 position, though moot here since inference is actually served by Decart, not Z.ai directly (next).

**Decart terms (`docs.platform.decart.ai/resources/terms-of-service`):** *"You shall not use the Materials to improve any large language model or other AI or machine learning system."* Same class of clause, same reading as Z.ai's above — judging is not improving a model. Separately: *"Decart.ai may use Content to develop, improve (including to train our AI models)"* — Decart, not Z.ai, is the one whose training-on-input policy actually governs our submitted case text and the four models' response text, since Decart is the literal inference host for this route. **Consequence, disclosed rather than treated as blocking:** unlike Gemini (G-1), this is not a scored-model contamination risk — the judge is not under test, and a judge that has partly memorised a case's gold answer is if anything more likely to score it correctly, not less. It is a smaller, separate disclosure: test-case text may enter Decart's training data via this route, on top of the existing Gemini exposure, which is immaterial for the same reason already stated in JUDGE-RUN-PLAN.md's data-policy note — everything here is published anyway (Decision C4), so there is nothing to leak beyond what publication already creates.

**Conclusion: `z-ai/glm-5.2:free`, served by Decart, is permitted for the judge role, with the same "plain-reading, conservative-where-ambiguous" caveat this file applies throughout — no provider bars evaluation/judging use, no provider bars publication.** Zero-balance callability is unverified by an actual call (deliberately — this review was to complete before any call was spent, per this session's instructions); it is the first thing checked when the 20-item re-judge starts.

**Standing rule added:** rule 6 below (re-review at every quarterly refresh) now also covers the judge, not just the four scored providers — the same standing-behaviour risk O-1 already put on record applies to any `:free` route.

---

## §5.1b model-terms flow-down · Judge model switched to MiniMax-M3 — 2026-08-28, same day

**Trigger:** `z-ai/glm-5.2:free`'s sole serving provider, Decart, returned `upstream_provider_shared_pool` 429s on **15 of 15** attempts across 7.5 minutes — the identical failure signature already on record for OpenRouter's benchmarked model (2026-08-17 finding), and severe enough (flat `retry_after_seconds: 5` regardless of elapsed wait) to read as a sustained capacity outage rather than brief contention. Zero items were judged before this was caught — no partial file, no mixed-judge contamination. Per the same escalation logic as §5.1 (don't retry a structural problem indefinitely; switch rather than stall), and confirmed with the user before any judge call was made under the new model, per the same "no silent judge swap" discipline JUDGE-RUN-PLAN.md §4 already states for local judges.

**Pick: `minimax/minimax-m3:free`** (MiniMax, 428B-total/23B-active MoE, 1M context, canonical slug `minimax/minimax-m3-20260531`). Confirmed live with a real 200 response at the moment of switching (unlike the deliberately-untested GLM-5.2 pick in §5.1, this one *was* verified working before committing, since the whole reason for switching was an availability problem). Independent of every benchmarked provider and architecture, same as GLM-5.2. Weaker reported reasoning index than GLM-5.2 (Artificial Analysis Intelligence Index 45 vs. GLM-5.2's reported 52.6), but still far above 7B class and was already the stated second choice in §5.1.

**Upstream serving provider — checked, not assumed, same method as §5.1.** `/api/v1/models/minimax/minimax-m3:free/endpoints` shows exactly **one** provider: **GMICloud** (`gmicloud/fp8`, fp8-quantized, 1,048,576-token context — the full native context, unlike GLM-5.2's free route which was capped to 256K).

**MiniMax terms (`platform.minimax.io/protocol/terms-of-service`, fetched via rendered page — this is a client-side app and the raw HTML/a summarizing fetch both return only the page shell, not the terms text; confirmed by browser rendering).** Searched the full rendered text for every clause pattern found in the other three providers' terms (`compete`, `competing`, `distill`, `benchmark`, `train a`/`training a`, `rate limit`, `scrap`/`crawl`/`robot`, `publish`) — **zero matches.** MiniMax's Open Platform terms carry no train-a-competitor clause, no benchmarking restriction, and no publication restriction at all — the only relevant clause is a data-use one: *"you retain your ownership rights in Client input and generated content. We may use the input and generated content to provide, maintain, develop, and improve our Services."* Same class of disclosure as Decart's in §5.1 (test-case text may enter MiniMax's training data via API use) and immaterial for the identical reason — everything here is published anyway (Decision C4).

**GMICloud terms — two separate documents, both checked, both clean.** (1) `gmicloud.ai/en/terms-and-conditions` — general Site terms; explicitly scoped to "the Site" throughout, anti-scraping clause reads the same as OpenRouter's and Decart's own equivalents (aimed at the web app, not API use) — no train/compete/benchmark/publish clauses found on a full-text keyword search. (2) `console.gmicloud.ai/user-policy` — an Acceptable Use Policy, but content-safety only (hate speech, harassment, illegal activity, fraud) — same class and scope as Mistral's "content-only usage policy," already the cleanest of the original four. Nothing here touches benchmarking, evaluation, or publication either.

**Conclusion: `minimax/minimax-m3:free`, served by GMICloud, is permitted for the judge role — actually the cleanest terms pairing found across every provider reviewed for this project, GLM-5.2/Decart included, since neither MiniMax nor GMICloud carries a train-a-competitor clause at all.** Zero-balance callability **is** verified (a live 200 response was already obtained while diagnosing the GLM-5.2 outage, since checking availability was the reason for looking at this candidate at all — this deliberately breaks from §5.1's "no call before go-ahead" discipline, because the call being verified here is a fallback-availability check made *after* the user had already approved starting the judge run, not before it, and no calibration item was scored by it).

**Standing rule:** the §5.1 standing rule (re-review at every quarterly refresh) now applies to this pick instead — `minimax/minimax-m3:free` via GMICloud is the currently pinned judge, not GLM-5.2/Decart.

---

## Findings noted, no action needed

- **Gemini — regional restriction.** EEA / Switzerland / UK require Paid Services. India is unaffected. Do not run the benchmark from a VPN endpoint in those regions.
- **Gemini — "not for consumer use."** Framed as developer/professional use; a published technical benchmark sits comfortably inside that.
- **Gemini — no competing models.** Prohibits developing models that compete with Gemini and reverse-engineering weights. Benchmarking does neither.
- **Groq / OpenRouter — no multiple accounts.** Already project policy: one account per provider, no key rotation, no IP rotation.
- **OpenRouter — model-terms flow-down (§5.1).** Each model carries its own provider's terms, which he is responsible for reviewing. If OpenRouter survives O-1, record which specific free models are used and confirm each one's terms.
- **OpenRouter — no competing service (§7).** The advisor *recommends* a stack; it does not route traffic or resell API access, so it is not a competing service. Worth re-checking if the product ever gains actual routing.
- **OpenRouter — no scraping the Site.** Applies to the website, not the API. All data here comes from API responses.
- **Mistral — content-only usage policy.** Prohibitions are all about generated content (illegal, hateful, fraudulent, misinformation, unqualified professional advice). Nothing touches benchmarking, measurement, or publication. Cleanest of the four.
- **Ollama.** Local, no service terms. The *model weights* carry their own licence — record which model and licence is used, and check it permits publishing benchmark results (Llama-family licences do; some research-only weights do not).

---

## Standing rules for the run

1. One account per provider. No key rotation, no IP rotation, no VPN, no circumvention of any kind.
2. Groq is never actively probed.
3. Publication of results only; no republication of provider documentation or site content.
4. Submitted text is original and non-sensitive — no personal, confidential, or client data reaches any free tier.
5. If a provider objects at any point, it is removed from the index immediately and the exclusion disclosed.
6. Terms are re-reviewed at every quarterly refresh; this file gets a new dated section, not an edit.

---

## Changelog

| Date | Change |
| :---- | :---- |
| 2026-08-28 | **§5.1b — judge switched to `minimax/minimax-m3:free` (served by GMICloud).** GLM-5.2's sole provider (Decart) hit a sustained 429 outage (15/15 attempts) before any item was judged. MiniMax's and GMICloud's terms reviewed and found cleaner than every other provider checked for this project — no train-a-competitor clause at all. |
| 2026-08-28 | **§5.1 flow-down addendum for the judge model.** `z-ai/glm-5.2:free` (served by Decart) proposed as the hosted judge after the local `qwen2.5:7b`/`14b` route closed (JUDGE-RUN-PLAN.md §4b). Both Z.ai's and Decart's terms reviewed; neither bars evaluation/judging use or publication. Closes the flow-down action item deferred 2026-08-13. |
| 2026-08-13 | Initial review of all four providers. Closes open question 2. Raises O-1 as a blocking item. |

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
| 2026-08-13 | Initial review of all four providers. Closes open question 2. Raises O-1 as a blocking item. |

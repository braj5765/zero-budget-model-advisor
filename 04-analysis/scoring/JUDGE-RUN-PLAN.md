# Judge Run Plan — clustered execution

**2026-08-20 · Owner: Braj**

The judge runs on CPU-only Ollama at roughly **6 minutes per item**. A full pass as rubric §4 specifies (4 models × 100 cases × 3 runs = 1,200 responses) is ~120 hours and is not executable. This file records how the run is split and what must stay true across the splits.

---

## 1. Scope of the judged set

**Judge `run_index = 1` only — 400 responses.** Nondeterminism is measured separately by judging all three runs for a **10% random sample (40 responses, recorded seed)**, rather than by median-of-three across the whole set.

This is a **rubric §4 amendment** and must be logged there before the full run starts. The trade, stated plainly for publication: quality scores come from a single run, with run-to-run variance reported from a subsample. Arguably more informative than median-of-three, which averages variance away instead of measuring it — but it is a weaker guarantee per score and belongs in Known Limitations either way.

Budget: 440 responses × ~6 min ≈ **44 hours**, before the speed measures in §3.

---

## 2. Clustered execution — the harness pattern, reused

The judge runner is **resumable and append-only**, identical in shape to `runner.py`:

- Output is **JSONL, appended**, never rewritten. One row per judged response.
- Resume key: **`(item_id or case_id, model_id, run_index)`**. Before each call, skip if that key already exists in the output file.
- **`--minutes N`** budget flag: judge until the budget is spent, finish the item in flight, exit cleanly. This is what makes a 45-minute session at the desk a useful unit of work.
- On startup print: resolved output file, count already judged, count remaining, estimated sessions left.
- A killed session loses at most one item. Ctrl-C mid-item is safe.

**Run identity resolves the same way as the harness:** explicit id wins, `--new-run` forces fresh, default resumes the most recent file. A judge pass spanning two weeks of short sessions is the expected case here, not the edge case — a date-derived default would re-judge everything.

---

## 3. Speed measures — apply before concluding 44 hours is the real number

Four changes, none of which touch what is measured:

1. **Keep the model resident.** `OLLAMA_KEEP_ALIVE=30m` (or `keep_alive` per request). A cold reload between calls can dominate a 6-minute figure; this may be the single largest win.
2. **Cap judge output.** `num_predict` sized to the JSON reply plus justifications. Generation dominates CPU time, and an uncapped judge that rambles costs minutes per item for tokens nobody reads.
3. **Set `num_ctx` explicitly** to comfortably exceed the longest assembled prompt. **Verify this before a long run** — a default context smaller than the prompt silently truncates, which is a correctness bug, not a speed one. Truncation would drop the anchors or the response and produce scores that look valid.
4. **Group items by task.** The large constant prefix (scale, dimensions, anchors, n/a rule) is identical within a task, so KV-cache reuse across consecutive same-task calls is real. This does **not** compromise §5 order randomisation: each item is judged in a fresh context with nothing carried between calls, so order effects are removed structurally rather than by shuffling. Record that grouping was used and why.

Re-measure per-item time after these before planning the session count.

---

## 4. What must stay true across sessions

A run split over many days introduces failure modes a single run doesn't have:

- **Pin the judge and record it per row.** `model_id`, tag **and digest** (`ollama list` ID) on every judged row. If the digest changes mid-pass — an Ollama update, a re-pull — **abort rather than continue**. Two judges in one dataset is silent corruption, and rubric §5 requires a pinned judge version per index release.
- **Pin the prompt version.** Record `judge_prompt_version` per row. It is v1.1 now; if it changes mid-pass, the affected rows are re-judged, not mixed.
- **Rubric version per row** (v1.4).
- **No mid-run rubric or prompt edits.** If either needs to change, the pass restarts under a new run id. `/03-results` and the judge output are both append-only; nothing is deleted.
- **Never retry a judge failure into a success** — *revised 2026-08-29, production pass: this rule does not mean what it first appears to mean, and got it backwards for one case.* The harness's no-retry-on-failure rule exists to stop a *benchmarked model's* failure rate from being laundered away — retrying `RATE_LIMIT` until a benchmarked model finally answers would hide how often it actually fails in practice, and that failure rate is itself a published finding about the model. **A judge call failure is not that.** `RATE_LIMIT`/`API_ERROR`/`MALFORMED` on the *judge*'s own transport is instrumentation failure — noise about whether OpenRouter's shared pool was congested at the moment of the call, not a fact about Gemini, Groq, Mistral or Ollama's output quality. There is nothing to launder, because a judge failure was never going to be published as a finding about any of the four models. So: **a judge attempt that fails is retried — on the next resume, by appending a fresh row for the same `(case_id, model_id, run_index)`, never edited in place.** A row's status is only "done" (skipped on resume) once its *latest* row for that key is a success; a failed row is left as a permanent record of that attempt, but does not block a later attempt. **`/scoring` must therefore read the latest row per key**, same convention already established for `probe.jsonl` (2026-08-17 finding: take the latest row per `model_id`, treat superseded ones as historical, not authoritative). What the pinning/abort rule above still means unmodified: an unrecoverable, structural problem with the judge itself (a digest change, a provider-identity mismatch) still halts the whole pass rather than producing failure rows, because that is a validity problem with every row the pass produces, not a one-off transport blip.
- **Prefer slow over lost calls.** The production pass measured a sustained ~26% failure rate (mostly `RATE_LIMIT`) at the unpaced call rate that had been clean in a 20-row sample — the shared pool's limit tracks request rate, not per-call latency, so a burst of fast calls (e.g. short classification prompts) can exceed it even when mean latency looks fine. `judge_common.MIN_INTERVAL_S` (an unconditional pre-call delay, same shape as the harness's own `base.pace()`) was raised from 0 to 5s in response; raise it further if the resumed pass still shows a sustained, not merely occasional, `RATE_LIMIT` rate.

---

## 4b. Judge escalation — resolved path, 2026-08-28

**`qwen2.5:7b` failed the gate twice and 14b is not runnable on this machine (~9GB, insufficient RAM/disk). The local-judge route is closed.**

Evidence, all retained and publishable:

| | κ | AC1 | raw agreement | ≥2-pt disagreements |
| :---- | :---- | :---- | :---- | :---- |
| 7b · prompt v1.1 | 0.223 | 0.756 | 77.6% | 10 |
| 7b · prompt v1.2 | 0.300 | 0.768 | — | 7 |

Two targeted prompt fixes bought +0.077 against a gap of 0.30, and **introduced a new failure** — the judge began marking `n/a` at its own discretion, violating §3.6 rule 1, which it had previously respected. That is instruction displacement: a 7B attending to new text at the cost of old. Further prompt iteration is not a route to 0.6.

Residual failures are capability-class, not wording-class: the judge denied a response abstained when it literally contained `INSUFFICIENT CONTEXT`, and did not apply the conditional coverage cap despite the anchor being carried verbatim.

**Order of attack from here:**

1. **Enforce `n/a` in code, not in the prompt.** `/scoring` knows from each case's `gold.notes` which dimensions are n/a-eligible. Reject any unsanctioned `n/a` and log it as a protocol violation. §3.6 rule 1 is a hard constraint and belongs in code; this removes a failure class for any judge and costs no prompt budget.
2. **Hosted free judge outside the benchmark set.** Gemini, Groq and Mistral are disqualified — they are scored models and would self-judge. **OpenRouter is now eligible**: it was cut from scoring (Decision A5), so no model it serves is under test, and the self-preference conflict does not arise. Pick a substantially larger free model, add a dated §5.1 model-terms addendum to `ToS-Review.md`, then **re-run the 20-item gate only** — 20 calls fits inside a 50/day cap, so this costs hours, not days. Changing the judge requires re-calibration; the gate is per judge.
3. **If that clears 0.6:** full 400-item pass, clustered against the provider's daily cap.
4. **If it does not:** fall to the pre-committed reduced set in §5.

*Data-policy note: a hosted judge sends test cases and model responses to a third party. Immaterial here — everything in this index is published anyway (Decision C4), so there is nothing to leak and no contamination risk beyond what publication already creates.*

### Steps 1–2 executed, 2026-08-28 (third session) — closest result yet, still short

Step 1 done: `judge.py`'s `na_eligible_dimensions()` derives n/a-eligibility from case structure (the classification no-correct-label shape and the json-output unparseable-response rule are the only two sanctioned cases in the 100-case set) and rejects anything else as a per-row `na_protocol_violations` flag, checked in `agreement.py`.

Step 2 done, with an unplanned detour: `z-ai/glm-5.2:free`'s sole provider (Decart) hit a sustained `upstream_provider_shared_pool` outage (15/15 attempts, ToS-Review.md §5.1) before any item was judged, so the pick was switched — with the user's go-ahead and a fresh terms review — to `minimax/minimax-m3:free` (GMICloud, ToS-Review.md §5.1b). All 20 items judged under `judge_prompt.md` v1.2, unchanged from the 7b re-judge:

| | κ | AC1 | raw agreement | ≥2-pt disagreements |
| :---- | :---- | :---- | :---- | :---- |
| 7b · prompt v1.1 | 0.223 | 0.756 | 77.6% | 10 |
| 7b · prompt v1.2 | 0.300 | 0.768 | — | 7 |
| MiniMax-M3 (hosted) · prompt v1.2 | **0.591** | 0.796 | 81.6% | 6 |

**Does not clear 0.6. Per this file's own step 3/4 branch, that routes to step 4 (the pre-committed fallback below) — but the failure profile changed enough to be worth stating plainly before that's triggered.** All 6 remaining disagreements audited in `04-analysis/calibration/disagreement_audit_hosted.md` are **prompt/anchor ambiguity, zero judge incapacity** — unlike both 7b runs, nothing here is the judge misreading text in front of it. 4 of the 6 sit on one item and trace to two causes: an over-broad reading of a claim-specific causation ban, and the coverage cap-rule miss reproducing *identically* on a materially stronger model — confirming the missing case-level `probes` field (§5.1's coverage anchor names it as a valid source for "the probed point"; `judge.py` has never assembled it into the prompt, on either judge) is a real, judge-independent input gap, not a capacity ceiling. The 6th is a genuine rubric gap: precision vs. normalisation don't have a stated owner for "arithmetically wrong unit conversion." **Prompt deliberately not touched this session, per instruction, to isolate the judge-switch effect** — whether to spend one more sharpening pass (surface `probes`, tighten the causation anchor to name only the specific forbidden claims) before falling to the reduced hand-scored set is the next decision, not made here.

### One bounded input-gap fix, 2026-08-28 (fourth session) — gate cleared, κ = 0.650

**This pass was authorized narrowly, and the distinction matters for how the result should be read: it was a targeted fix for a diagnosed input gap (the coverage anchor names `probes` as a valid source; the prompt never supplied it), not a prompt-iteration attempt on the failing 0.591 result above.** The instruction was explicit that nothing else could move — no new anchor, no reworded anchor, no dimension-table change, and the precision/normalisation boundary gap (this file's own note above) stays open on purpose. This is the distinction rubric §5's "sharpen anchors, re-judge, retry" step exists to prevent being confused with: that step is for chasing a number, this one was for correcting a prompt that omitted an input its own anchor already required.

`judge_prompt.md` → v1.3: `{{PROBES}}` added to §A ahead of `{{GOLD_NOTES}}`. Falsification test recorded in the changelog before the re-judge: adding `probes` cannot move any human score, since the human scorer already had it. Re-judged the same 20 with the same judge (`minimax/minimax-m3:free`, GMICloud):

| | κ | AC1 | raw agreement | ≥2-pt disagreements |
| :---- | :---- | :---- | :---- | :---- |
| 7b · prompt v1.1 | 0.223 | 0.756 | 77.6% | 10 |
| 7b · prompt v1.2 | 0.300 | 0.768 | — | 7 |
| MiniMax-M3 (hosted) · prompt v1.2 | 0.591 | 0.796 | 81.6% | 6 |
| MiniMax-M3 (hosted) · prompt v1.3 | **0.650** | 0.779 | 80.3% | 4 |

**Clears 0.6.** Audited in `disagreement_audit_hosted_v1.3.md`: 4 of 4 remaining disagreements are prompt ambiguity, zero judge incapacity. The fix's effect is verifiable, not assumed — one dimension's justification now uses language ("the case was designed to probe against") that only makes sense if `probes` reached the judge — but it didn't fully close the coverage-cap miss on `cal-14`: the judge now demonstrably knows the case's trap without connecting that fact to the specific anchor rule that acts on it, an input gap closed sitting next to a reasoning-chain gap that isn't. Per instruction, **stopped here — the full 400-item pass was not started.** Triggering it is the user's decision.

### Pre-committed fallback — defined now, before the next κ is seen

If no judge clears 0.6: **hand-score a reduced set. 5 cases per task, stratified 3 typical / 1 hard / 1 adversarial, × 4 models = 100 responses**, drawn with a recorded seed, scored blind against rubric v1.4. Published with n stated per task and the reduction disclosed as a limitation.

Fewer cases with real scores beats full coverage from an uncalibrated judge. **The 0.6 threshold does not move**, and this fallback is fixed here so the choice cannot be shaped by disappointment at a later number.

---

## 5. If clusters still don't fit

In preference order, and only after §3 is measured:

1. **Cut the nondeterminism subsample** from 10% to 5%. Cheapest concession; weakens variance estimate only.
2. **A hosted free judge outside the benchmark set.** Gemini, Groq and Mistral are all disqualified — they are scored models and would self-judge. OpenRouter is cut from scoring but its shared-pool contention makes it unreliable; resumability tolerates that, so it is viable if nothing better exists. Any new provider needs a terms review appended to `ToS-Review.md` first.
3. **Reduce cases per task.** Last resort — n=20 is already stated as thin in Known Limitations, and cutting it undermines the headline claim rather than a supporting one.

**Not on the list: lowering the κ threshold, or skipping the calibration gate.** Those are the credibility of the whole index.

---

## 6. Held-out generalisation check — pre-registered 2026-08-29, before any item is scored

**The problem.** κ=0.650 (S4b, above) was measured on the same 20 calibration items the judge prompt was iterated against four times (v1.1 → v1.2 anchors → judge swap → v1.3 probes fix). There is no held-out set, so that figure is an optimistically biased estimate of judge/human agreement, by an unknown amount. This section fixes, in advance, how a fresh 20-item measurement is read — so the reading cannot be shaped by the number once it exists, the same discipline Rubric §5's 2026-08-19 subsection applies to the kappa-paradox reading rule.

**The set.** `calibration/sample_heldout.json` — 20 fresh (case, model) pairs, drawn `draw_heldout_sample.py`, seed `20260829`. Excluded by `case_id`, not by pair: any of the 20 case_ids in `calibration/sample.json` is out regardless of which model it is paired with here, because the v1.2/v1.3 prompt changes were driven by those specific cases' content (cal-14's probes, cal-01's label line, cal-16's precision/normalisation boundary) and reusing a case_id under a different model would leak exactly the overfitting being measured. 20 of 100 case_ids were already spent on the in-sample set; **80 remained available**, and the held-out 20 are drawn from that pool. Same stratification rule as the original: all five tasks, all three difficulty tiers, all four scored models, OpenRouter excluded (Decision A5). Model identity is sealed in `sealed_model_map_heldout.json`, not readable from the scoring sheet.

**Adversarial task composition is fixed to match `sample.json`, not redrawn — a stated design constraint, not an oversight.** `sample.json`'s three adversarial-slot tasks are `{extraction, rag-qa, summarization}`. `draw_heldout_sample.py`'s `ADVERSARIAL_TASKS` constant pins the same three, rather than sampling a fresh 3-of-5 each draw. Reason: summarization is the least-stable, worst-agreeing task across every calibration run recorded in this file — 36–60% median-identical, 5 of the 6 v1.2 disagreements, cal-14's coverage-cap miss still open in v1.3 — while json-output is the most stable. A held-out set that happened to swap summarization's adversarial slot for json-output's would be easier on exactly the slice the prompt was tuned against, biasing held-out κ upward toward the reassuring result, for reasons having nothing to do with generalisation. **This makes the held-out set a matched comparison against one specific prior sample, not an independent representative draw from the case universe** — the two are comparable only because their hard cases sit in the same tasks. Recorded here rather than left implicit.

**Discarded first draft, logged rather than deleted.** The first run of `draw_heldout_sample.py`, seed `20260829`, sampled the 3-of-5 adversarial tasks randomly rather than fixing them, and landed on `{extraction, json-output, rag-qa}` — swapping summarization's adversarial slot for json-output's relative to the in-sample set. Replaced before scoring, for the reason above: it would have biased the comparison in the reassuring direction, on the specific slice most likely to disagree. `sample_heldout.json`, `sealed_model_map_heldout.json` and `scoring_sheet_heldout.json` were regenerated with `ADVERSARIAL_TASKS` fixed; same seed, same exclusion pool, same 12/5/3 and per-model balance, only the adversarial task set changed.

**The panel — reported together, exactly as S4b's calibration runs are, so the two numbers are comparable:** quadratic-weighted Cohen's κ, Gwet's AC1, raw agreement, the count of ≥2-point disagreements, both raters' marginal distributions, and the full confusion matrix. Computed with `agreement.py`, unmodified in method — pointed at the held-out files rather than the in-sample ones.

**The judge.** `minimax/minimax-m3:free` (GMICloud), **`judge_prompt.md` v1.3, frozen.** This is a measurement of that exact judge configuration, not a fresh calibration attempt — nothing about the prompt, the rubric, or the judge model changes before or during this pass.

**Response, fixed now — this is Braj's intent, stated as his, before any held-out score exists:**

| Held-out κ | Reading | Action |
| :---- | :---- | :---- |
| ≥ 0.6 | Generalises | Held-out result confirms it; the in-sample κ=0.650 stands as reported, alongside the held-out figure. |
| 0.45 – 0.6 | Real overfitting, not catastrophic | Published as a finding, not smoothed over. Triggers Rubric §5's hand-scoring fallback (JUDGE-RUN-PLAN §4b's pre-committed reduced set) for the tasks where the held-out disagreement concentrates. |
| < 0.45 | In-sample gate does not hold | The κ=0.650 pass is treated as invalidated. The index ships hand-scored on the reduced set per §5, in full. |

**Pre-commitment: no v1.4.** The v1.3 judge prompt is frozen for this measurement. If the held-out result is disappointing, the response is the table above — the fallback, or the disclosure — **never a prompt edit made in response to seeing the number.** Iterating the prompt after seeing held-out performance would convert this held-out set into a second calibration set, spending the only clean generalisation measurement this project can make. There is no third set to fall back to if this one is burned.

**Disagreement audit still applies regardless of κ**, per Rubric §5 rule 4: every ≥2-point gap in the held-out set is audited and written up in `calibration/disagreement_audit_heldout.md` before the result is reported, exactly as the in-sample audits were.

---

## 7. What is and isn't independently attested

**`git log` runs to 2026-08-19** (`e33d7cd`, "Close open question 1: local Qwen judge; A5 logged"). Everything after that — this file's own §4b escalation path and its four dated re-judge sessions, the rubric's v1.3 through v1.7 amendments, §4b's same-day amendment-then-revert of the judged scope, and this section's own §6 pre-registration and no-v1.4 pre-commitment — was committed on **2026-09-03**, in one batch of seven commits, alongside the held-out run and everything downstream of it.

**What that means concretely:** every date attached to a decision in this file (2026-08-20, -28 ×4, -29, -31) is an in-file claim, not a git-attested one. Git can confirm that this content exists now, on 2026-09-03, and that it postdates `e33d7cd`. It cannot confirm that v1.3 was really written before v1.4, that §4b's revert really happened the same day as its amendment, that §6's pre-registration table really predated any held-out item being scored, or that any other internal ordering this file asserts is the order things actually happened — because no commit exists at any of the intermediate points that would let a reader check one claimed date against another independently.

**A reader who does not trust the in-file dates has no independent check on the ordering for the 2026-08-19 → 2026-09-03 window.** This is stated plainly rather than left for someone to discover by noticing the commit graph doesn't match the prose. It is a real limitation of the evidence this project can offer for that window, not a limitation of the process that produced the work — the pre-registration discipline itself (writing the response before seeing the number, freezing the prompt before a run, reverting an amendment whose premise failed) was followed either way; what's missing is a third party's ability to verify from the repository alone, rather than from the author's word, that it was followed in the order claimed. Disclosed here and in Known Limitations, not papered over.

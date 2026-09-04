# Refresh Procedure

**Required, not optional.** Decision C2 rests on maintenance being what keeps this index honest — a dated index that goes stale is worse than no index. `04-analysis/build_advisor_index.py` now also emits `05-site/data/index.data.js`, a published, user-facing asset — a refresh that stops partway through publishes numbers the live site actually shows, not just a file sitting in the repo. Follow this in order. Every command is run from the repo root unless stated otherwise.

---

## 0. Before you run anything

These are judgment steps, not scripts — nothing technical enforces them, which is exactly why they're listed first and in writing.

1. **Re-review terms.** Per `00-planning/ToS-Review.md` standing rule 6: re-review all four scored providers' terms, plus the currently pinned judge's (provider + serving infrastructure — see that file's §5.1/§5.1b for the pattern: check the model's *and* its upstream serving provider's terms separately, they can differ). **Add a new dated section to `ToS-Review.md`; do not edit the existing ones.** If any provider now objects, remove it and disclose per standing rule 5.
2. **Rotate cases.** Per `01-rubric-and-testcases/Test-Case-Design.md` ("Rotation") and Decision C4: replace **~25% of cases** in `01-rubric-and-testcases/cases/*.json` before this run, not after — Gemini trains on free-tier input, so an unrotated set risks scoring partly on memorisation by the run after next. Keep the 12/5/3 typical/hard/adversarial stratification in whichever files you touch.
3. **Confirm the judge is pinned, deliberately.** Current pin: `minimax/minimax-m3:free` via GMICloud, prompt v1.3 (`00-planning/ToS-Review.md` §5.1b, `04-analysis/scoring/judge_prompt.md`). Rubric §5 requires one pinned judge model *and version* per index release. If you are changing either, that forces a fresh calibration cycle, not a patch — this is a decision, make it before step 2 of the sequence below, not discovered partway through.
4. **Calibration set is already decided — don't re-decide it.** Per `04-analysis/Known-Limitations.md` §3: the "Set 3" items drawn for a third calibration round are earmarked to become **this refresh's** calibration set, judged under Rubric v1.9's consolidated specification (§3.3–§3.5) on both legs — human and judge — for the first time. Use them; don't draw a new sample unless Set 3 has already been consumed by a prior refresh, in which case draw a fresh one the same way `04-analysis/scoring/draw_heldout_sample.py` drew the held-out set (same stratification rule, excluding every case_id already used in any prior calibration sample).

---

## 1. Re-run the benchmark

```
python 02-harness/runner.py --new-run
```

Reads `02-harness/config.toml` by default (`--config` to point elsewhere). Resumable — if it stops partway, re-run with `--run-id <the id it printed>` rather than `--new-run` to continue the same file instead of starting a second one. Writes `03-results/run-<id>.jsonl`.

**Then, and only then** (never before, never concurrently — `02-harness/probe.py`'s own docstring is explicit about this):

```
python 02-harness/probe.py
```

Gated per-provider on `probe_allowed` in `config.toml` — Groq is never probed (ToS-Review standing rule 2). Writes/appends `03-results/probe.jsonl`.

**Append-only, both files.** `03-results/` is never edited or overwritten — a new run gets a new dated `run-*.jsonl`; `probe.jsonl` is appended to, not replaced.

---

## 2. Re-judge

Hand-score the refreshed calibration set (step 0.4) first, working from the rubric alone, before running the judge on it — Rubric §5 step 1, same order as every prior calibration round. Compute κ per §5's decision rule table before proceeding; if it doesn't clear the gate, that is itself a finding to record (see `Known-Limitations.md` §1 for what the last one looked like), not something to route around.

Once the gate decision is made:

```
python 04-analysis/scoring/judge_production.py --new-run
```

`--minutes N` spends a time budget and exits cleanly after finishing the item in flight; `--limit N` stops after N new rows regardless of time; omit both to run to completion. Resumable the same way as the runner (`--run-id` to continue a specific file; default resumes the most recent file in `04-analysis/production/` if you omit both `--new-run` and `--run-id`). Writes `04-analysis/production/judge-run-<id>.jsonl`.

**Append-only.** A failed attempt is never edited in place — `/scoring` reads the *latest* row per `(case_id, model_id, run_index)` key, per the same convention `probe.jsonl` already uses (see `judge_production.py`'s own docstring for why a judge-call failure is retried by appending, never by overwriting).

---

## 3. Aggregate

```
python 04-analysis/aggregate.py
```

**Manual step required first, or this silently scores the wrong run.** `aggregate.py` currently hardcodes `JUDGE_FILE` and `RUN_FILE` as specific filenames near the top of the script — it does not discover "the latest run" on its own. Edit those two constants to point at the filenames step 1 and step 2 just produced before running it. This is the single most likely way a refresh publishes stale numbers without any error being raised: the script runs, exits 0, and silently re-aggregates last quarter's data if you skip this edit.

Writes `04-analysis/scores.json` and `04-analysis/scores-summary.md`.

---

## 4. Build the site data

```
python 04-analysis/build_advisor_index.py
```

Reads `scores.json`, writes `05-site/data/index.json` **and** `05-site/data/index.data.js` together, from the same in-memory object, in the same pass — this is what makes step 5 below meaningful rather than hopeful.

---

## 5. Verify before publishing

1. **Confirm the two generated files agree.** Both carry a `generated_at` stamp; they were just written from the same object, but this is the mechanical proof, not an assumption:
   ```
   grep generated_at 05-site/data/index.json 05-site/data/index.data.js
   ```
   Both lines must show the identical timestamp. If they don't, something touched one file after generation — do not publish; re-run step 4.
2. **Serve the site over HTTP and look at it.** `file://` is fine for the four non-advisor routes but `index.html` needs a server (Decision C1 amendment, 2026-09-05 — Chrome/Edge block ES-module imports over `file://`). From `05-site/`: `python -m http.server`, then open `/`, `/results.html`, and at least one `/model.html?id=` in a browser. Confirm no red data-integrity banner appears anywhere (that banner is `site.js`'s `checkDataFreshness()` catching exactly the drift step 5.1 checks for by hand — seeing it live means step 5.1 was skipped or something changed between the two checks).
3. **Spot-check one figure against `scores-summary.md`** — pick any model × task cell on `/results` and confirm it matches the corresponding row in the freshly written summary, as a sanity check that step 3's manual file-path edit actually pointed at the new run and not a stale one.

---

## 6. Publish

Commit, in one changeset: the new `03-results/run-*.jsonl` (and `probe.jsonl` if it changed), `04-analysis/production/judge-run-*.jsonl`, `04-analysis/scores.json`, `04-analysis/scores-summary.md`, `05-site/data/index.json`, `05-site/data/index.data.js`, and the new dated `ToS-Review.md` section from step 0.1. Push to whatever branch GitHub Pages serves from (Decision Q4) — there is no separate deploy step; Pages serves the repo directly.

Ship the `/about` changelog entry naming what changed this refresh (UX-and-Feedback-Spec §5, "the loop that closes") — including, if applicable, what feedback or disputes from the last quarter changed a score or a rubric anchor.

---

## What is not automated, and breaks silently if skipped

- **Step 0's three pre-checks** (ToS, rotation, judge pin) — nothing technical enforces any of them. A refresh that skips case rotation still runs cleanly and produces a number; it's just a number Decision C4's own rationale no longer backs.
- **Step 3's hardcoded `JUDGE_FILE`/`RUN_FILE` edit** — the most likely single point of silent staleness in this whole procedure. `aggregate.py` will not warn you; it will happily re-score last quarter's run.
- **The κ gate's decision rule (step 2)** — Rubric §5's table is a decision procedure, not a script. Whether a fresh calibration result clears the gate, is a prevalence artifact, or is a real failure is a judgment call against that table, the same way `Known-Limitations.md` §1 documents it being made (and missed) before.
- **Step 5's generated_at check** — `checkDataFreshness()` in `site.js` catches drift live on the deployed site, but that is a safety net for readers, not a substitute for checking before you publish.

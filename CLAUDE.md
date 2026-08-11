# Engineering Constitution — Zero-Budget Model Advisor

This file is the code-discipline contract for this repo. It is written to be dropped in as `CLAUDE.md` at the project root, so any AI assistant working on this codebase reads and obeys it automatically — that's the enforcement mechanism, not a wishlist.

**The failure this exists to prevent:** a 4-line change arriving as 30 lines of code. Verbose scaffolding, defensive wrappers nobody asked for, abstractions invented for a single caller, and helpers that exist because generating them felt productive.

---

## The prime rule

> **Write the smallest correct change. Then delete what isn't load-bearing.**

Every line must justify its existence. If a line can be removed and the code still does the job correctly, it was never needed.

---

## Non-negotiable rules

1. **Match the change size to the problem size.** A 4-line fix is 4 lines. If a small fix is producing a large diff, stop and explain why before writing it — that divergence is a signal something is being over-engineered or misunderstood.

2. **No speculative abstraction.** Do not write an interface, base class, config layer, or plugin system for a single implementation. Abstract on the **third** occurrence, not the first. Two duplicated blocks are cheaper than one wrong abstraction.

3. **No unrequested error handling.** Do not wrap everything in try/except. Handle errors where there is a real, known failure mode and a meaningful recovery. Let everything else crash loudly — a swallowed exception in a benchmark harness silently corrupts results, which is worse than a stack trace.

4. **No defensive parameter validation** on internal functions. Validate at the system boundary (API responses, config files, user input). Trust your own code.

5. **Read before you write.** Never add a function without checking whether one already exists. Duplicate helpers with slightly different names are how a small codebase rots.

6. **Edit in place; don't rewrite.** Modify the existing function. Do not regenerate a whole file to change three lines — it destroys review-ability and hides the actual change.

7. **No comments that restate the code.** Comment only *why*, never *what*. `# increment counter` above `counter += 1` is noise. `# Groq returns 429 without Retry-After; back off manually` is worth its line.

8. **No dead code, ever.** No commented-out blocks "in case we need it". That's what git is for.

9. **Standard library first.** A dependency must earn its place. Do not add a package to save six lines — every dependency is a maintenance liability on a project designed to be re-run quarterly for years.

10. **One responsibility per file.** If a file needs "and" to describe it, split it.

---

## Diff discipline

Before committing any change, state in one line: **what changed, and why that's the minimum.**

Rough size expectations — a diff exceeding these needs a stated reason, not an apology:

| Change type | Expected diff |
| :---- | :---- |
| Bug fix | < 10 lines |
| Small feature | < 50 lines |
| New module | < 200 lines |

If a "small feature" is running to 200 lines, the feature was underspecified or the design is wrong. Stop and re-scope.

---

## The refactor trigger

Refactor only when one of these is **actually true** — not when it feels tidy:

- The same logic appears a **third** time
- A file exceeds ~300 lines
- A function exceeds ~40 lines or takes more than 4 parameters
- A change requires editing 3+ files to make one logical modification

Absent one of these, leave it alone. Unprompted refactoring inflates diffs and hides real changes inside cosmetic ones.

---

## Project structure

```
/data          benchmark inputs — test cases, gold references (versioned, never edited in place)
/harness       runner: model clients, rate-limit probing, logging
/scoring       judge orchestration, rubric application, κ calculation
/analysis      results aggregation, breakeven modelling
/site          static site + client-side advisor
/results       run outputs, dated + versioned (append-only, never overwritten)
```

Rules that follow from this layout:

- **`/data` and `/results` are append-only.** Reproducibility depends on old runs remaining exactly as they were. A refresh writes a new dated file; it never mutates an old one.
- **The harness never knows about scoring, and scoring never knows about the site.** Dependencies point one way: `harness → scoring → analysis → site`. Any back-reference is a design error.
- **Model clients share one thin interface** — `call(prompt, config) → response | failure`. Provider quirks are absorbed inside each client, never leaked into the harness. This is the one abstraction justified up front, because there are five implementations on day one.
- **Config over code.** Model lists, rate limits, timeouts and paths live in one config file. Adding a sixth provider next quarter should be a config edit plus one client, not a hunt through the harness.

---

## Instructions for AI assistants working in this repo

- Before writing code, state your plan in 2–3 lines and the expected diff size. Wait for confirmation on anything above ~50 lines.
- Prefer `Edit` over `Write` on existing files. Rewriting a file to change a few lines is a rule violation.
- Do not add tests, docstrings, type hints, logging, or error handling that weren't asked for. Ask first — they may well be wanted, but they should be a decision, not a reflex.
- Do not create README files, example scripts, or `__init__.py` boilerplate unprompted.
- When finished, report **lines added / lines removed**, and flag any line you're unsure earns its place.
- If a request is ambiguous, ask one question rather than generating three variants.

---

## Definition of done

A change is done when: it works, the diff is the minimum that makes it work, nothing was added "for later", and it can be explained in one sentence.

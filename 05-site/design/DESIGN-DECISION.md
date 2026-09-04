# Design Decision — Zero-Budget Model Advisor site

**2026-09-03 · Braj, with design directions produced in-session · Status: chosen, fixed, ready to build against**

This is the file the build spoke works from. It is specific enough that building the five routes should require zero further design decisions — only implementation. If something here is ambiguous, that's a bug in this document, not an invitation to improvise.

---

## 1. Chosen direction

**Direction 1 — Field Notes.** Serif editorial register, warm paper ground, rust accent. Chosen by Braj after reviewing three complete directions (`05-site/design/index.html`) rendered against the same two real screens (advisor result, results matrix).

**Rejected:**

- **Direction 2 — Control Room** (monospace, instrument-panel register, indigo/teal, discrete 10-segment score meter). Read as more "benchmark tooling" than "portfolio showcase" — closer to a QA dashboard than a product a builder would trust for a recommendation. Its one genuinely reusable idea — a coarse, bucketed meter as a way of not overclaiming precision — is preserved in spirit by Field Notes' hatched uncertainty band, which does the same job (visibly declaring "don't read this to the pixel") without adopting the whole technical register.
- **Direction 3 — Studio** (warm humanist sans, card-based, coral/teal, rounded geometry). The stronger of the two rejected directions — closer in spirit to Field Notes — but the rounded-card, sans-only treatment read as more generic-SaaS than the register this project's content actually earns. A project whose headline finding is "we published our own judge's calibration failure" supports a more editorial, considered typographic voice than a rounded coral dashboard suggests.

Both rejected directions are left as-built in `05-site/design/` for the record. **No further design work happens in them.** All fixes, new screens, and this spec apply to Field Notes only.

---

## 2. The five product decisions (locked before any direction was drawn)

These existed only as chat decisions until this file — that's the reason this file exists at all; a decision that lives only in a conversation is not load-bearing for anyone who builds later.

1. **Score render: number + bar, with a visible uncertainty band.** A bar alone implies more precision than an n=20 sample supports (Known-Limitations §2.7); a number alone loses the at-a-glance scan a showcase register wants. Both together, with the bar carrying a visible band marking ±5 points — the threshold below which this index already declines to call a gap meaningful — resolve the tension by stating the imprecision in the same visual unit making the claim.
2. **Filter table: behind a disclosure, with a mandatory visible one-line summary.** Collapsed by default (`<details>`), because a persistent full table competes with the primary recommendation in this register. Amended into Decision Log C6 on 2026-09-03 specifically because the collapsed state must never look like "nothing to see here" — it always carries a real, data-driven headline (e.g. *"1 of 4 models filtered out — latency."*) so a reader who never clicks still learns that filtering happened and on what axis.
3. **Calibration disclosure: a site-wide, persistent, non-dismissible strip.** Present, identically structured, on every page that shows a score — not a per-page banner, not something a user can close. It is part of the masthead, not an alert: no dismiss control, no warning-triangle iconography, styled in the page's own palette rather than a generic "caution" color.
4. **Light theme only.** Matches `UX-and-Feedback-Spec.md` §6's existing v1 scope decision; re-confirmed rather than re-opened given the register change to portfolio-showcase.
5. **Card hierarchy: one clear primary pick plus up to two alternates, never three equals.** Matches what `advisor.js` actually returns (a distinct `primary` object plus an `also_survived` array) — visual equality would misrepresent a data shape that already has a ranking for the stated query.

---

## 3. Type

**Three families, one job each — never mixed within a single value:**

| Role | Stack | Used for |
| :--- | :--- | :--- |
| Display / body serif | `"Iowan Old Style","Palatino Linotype",Palatino,"Book Antiqua",ui-serif,Georgia,serif` | Headings, verdict text, prose, nav wordmark |
| Data / numbers | `ui-monospace,"SF Mono",Consolas,"Liberation Mono",monospace` | Every score, every ms/rpm/rpd figure, model IDs in the filter table, table cell values. Always `font-variant-numeric: tabular-nums`. |
| UI chrome | `-apple-system,"Segoe UI",Roboto,system-ui,sans-serif` | Labels, nav links, tags, badges, form inputs, small print — anything that is interface rather than content |

No web fonts. System stacks only — required by C1 (must work over `file://` with no build step and no network dependency).

**Scale actually in use** (base 17px / 1rem):

| Token | Size | Weight | Where |
| :--- | :--- | :--- | :--- |
| `--text-display` | 1.9rem | 600 | Methodology `<h1>` |
| `--text-h1` | 1.7rem | 600 | Advisor query line, Results `<h1>` |
| `--text-h2` | 1.4–1.6rem | 600 | Primary-card model name, section `<h2>` |
| `--text-score` | 3rem | 600 (mono) | The one large score number on the advisor card |
| `--text-h3` | 1.15rem | 600 | Sub-section headers |
| `--text-body` | 1rem (17px) | 400 | Prose, verdict text |
| `--text-stat` | 1.15–1.3rem | 600 (mono) | Stat-block values, alt-card scores |
| `--text-small` | 0.82–0.92rem | 400/600 | Nav, captions, form fields |
| `--text-micro` | 0.66–0.78rem | 600–700, uppercase, letter-spacing .05–.14em | Section labels, tags, table headers |

Line height 1.5 for body copy, 1.6 for the methodology page's longer-form prose.

---

## 4. Colour tokens

```css
--paper:        #faf6ee;   /* page background */
--paper-raised: #fffdf8;   /* cards, table body, panels */
--ink:          #1c1a16;   /* primary text */
--ink-soft:     #5a544a;   /* secondary text, captions, nav */
--rule:         #ddd2bd;   /* all hairline borders/dividers */
--rust:         #a8461f;   /* primary accent — score fills, active states, CTAs */
--rust-deep:    #7d3115;   /* accent text (score numbers, active tab, disclosure links) */
--sage:         #516b4c;   /* positive/pass state, fallback-box accent */
--sage-bg:      #e9efe4;
--brick:        #8f3226;   /* negative/fail state */
--brick-bg:     #f6e6e1;
--amber-bg:     #f4ecd8;   /* disclosure strip, active-tab, warm callouts */
```

Light theme only (Decision #4) — no dark-mode tokens to maintain. `color-scheme: light` should be set at the root when this becomes a real page so it doesn't inherit a dark OS preference by accident.

---

## 5. Spacing scale

The mockups used organic pixel values; formalise to an 4px base scale for the build:

```css
--space-1: 4px;   --space-2: 8px;   --space-3: 12px;  --space-4: 16px;  --space-5: 20px;
--space-6: 24px;  --space-7: 32px;  --space-8: 40px;  --space-9: 56px;  --space-10: 80px;
```

Card internal padding: `--space-7` to `--space-8` (32–34px, matches `.primary` in the mockups). Section gaps on a page: `--space-9` (56px, matches `.footnote` top margin). Grid gap between primary card and side column: `--space-8` to match `.layout{gap:40px}`. Table cell padding: `--space-4` (matches `14–16px` used throughout).

---

## 6. How a score renders

Number + bar + band, always together, never one without the others:

1. **Number** — mono, `--text-score` (3rem) on the advisor card's headline score, `--text-stat` (1.15–1.3rem) everywhere else (alt cards, results-matrix cells, dimension breakdowns). Colour `--rust-deep`.
2. **Bar** — a 6–9px track (`background:#ece2ce` / a paper-derived neutral), filled `--rust` to the score's percentage.
3. **Band** — a hatched (`repeating-linear-gradient(45deg, rgba(0,0,0,.14) 0 2px, transparent 2px 5px)`) overlay, width ≈10–11% of the track, centered on the score value (`left: calc(<score>% - 5.5%)`), representing ±5 points. **Every score render on every surface carries this band** — the advisor card, and (per fix 1 below) it is *not* required on the results-matrix bars, which are smaller and already carry the same "gap under ~5pts is noise" caption once per lens rather than once per cell; a per-cell band at 64px wide would be illegible. The rule: **the band is mandatory on any score rendered above ~120px of bar width; below that, the lens-level or card-level caption stating the ±5pt rule is the substitute.**
4. **Caption** — one line beneath, sans, `--text-small`/`--text-micro`, stating what n is and what the band means in words, not just visually. Never omit this even though the band is visual — a reader using a screen reader or skimming past the graphic still needs the number.

---

## 7. How each results-matrix lens renders (including the fix)

Four lenses, one shared table, one shared `render(lens)` function switching behaviour — this is a **single component with four data-bound states**, not four components.

- **Quality** (higher = better): standard bar, `--rust` fill, width = raw percentage. Cells are **clickable** — clicking opens a shared expansion panel below the table showing that model×task's real per-dimension breakdown, adversarial sub-score, n/a count, and a "Disagree with this score?" dispute mini-form (idle → thanks states). Only Quality cells are clickable; the other three lenses are read-only.
- **p95 Latency (a cost-like, lower-is-better lens) — the fix.** **Chosen approach: invert the fill.** The bar's fill percentage is computed as `(referenceMax − value) / referenceMax`, where `referenceMax` is the single slowest measured result on the whole grid (81,703ms — Ollama, extraction), **not** the raw value's own percentage. The displayed number beside the bar is always the true, real ms figure — only the bar's fill direction is inverted. This was chosen over the other two options considered (recolouring cost-like lenses with a "warning" palette; reversing the axis's printed scale) because it requires the reader to learn nothing new: **"longer/fuller bar = better" stays true on every lens on the page**, so a long, dark bar can never again be misread as good performance the way it did before the fix. A lens-specific hint line (see below) states this explicitly on-page. Do not compute this per-column (per-task) — one shared `referenceMax` across the whole lens keeps a model's own bar comparable across its five tasks, which per-column normalisation would break.
- **Success rate** (higher = better): identical rendering to Quality (same fill direction, same semantics — no fix needed here, it was never inverted). Because every cell is 100%, this lens carries a **mandatory annotation box above the table** (not per-cell) stating the finding in words — "All four scored models: 100% success..." — and linking to the excluded-provider panel. Never ship this lens without that annotation; a wall of "100%" with no comment reads as a broken table.
- **Rate-limit ceiling** (no bar; text + tag): two distinct render paths in the same lens, chosen per model:
  - **Constant-by-design models** (Gemini, Groq, Ollama): one cell, `colspan="5"`, centred, tinted background (`#f6f0e2` or equivalent), the ceiling value in bold plus an italic sans tag stating *why* it's constant ("request-capped — same ceiling regardless of task" / "self-hosted — no network ceiling to vary"). The colspan and tint are what signal "this is deliberate," not a copy-paste artifact — never render five identical left-aligned cells for these models.
  - **Genuinely task-varying models** (Mistral, or any future token-metered provider): five separate cells, one real derived figure per task, each tagged "derived from measured tokens — not a vendor figure" per Decision C5's labelling requirement. The visual contrast between one merged cell and five distinct ones *is* the "constant vs. varies" signal — don't add extra chrome to make this clearer; the structural difference already does it.

**Lens-hint line:** a single `<p id="lens-hint">` beneath the tab row, sans, `--text-small`, whose text swaps with the active lens. This is where the latency-inversion explanation and the ceiling dual-metering explanation live in the reader's own path, not buried in a tooltip. Required on every lens, including Quality (states "click a cell" there).

---

## 8. The excluded-provider panel

OpenRouter is not a row in the scored table (it has no quality data — Decision A5) and is not tab-dependent (it must be visible regardless of which lens is active, since fix 3/4's whole point is that a reader browsing *any* lens must be able to find it). Render it as a **persistent panel below the table and its footnote**, on every lens, id'd `#excluded` so the Success-rate lens's annotation can deep-link to it. Component: a tinted (`--brick-bg`) block with a small uppercase tag ("Excluded from quality scoring"), the reason (Decision A5, real numbers: 96/300, 32.0%), a three-stat strip (success rate / failure count / measured date), a prose paragraph on the two distinct ceilings, and a closing citation line to the source document. This exact component is reusable wherever a future refresh needs to disclose another excluded provider — don't build a second bespoke pattern for that case.

---

## 9. Disclosure placement

The κ=0.358 strip is part of `header.masthead`, immediately below the nav row, on **every** page (Advisor, Results, Methodology, and — per extrapolation — Model profile and About). Structure, fixed:

1. A small mono badge (`κ 0.358`) — not a warning icon.
2. One sentence: measured date, judge model + version, the number, the floor it missed, and the plain consequence ("the calibration gate is invalidated... published anyway, disclosed rather than hidden").
3. An inline `<details>` expansion ("What that means →") carrying the fuller paragraph (in-sample vs held-out, the spec-gap caveat, the reading instruction) — present on the Advisor and Results pages as a compressed entry point; **omitted on Methodology**, where the strip's own sentence says outright "this entire page is that disclosure, in full" rather than linking to itself.

Never a dismiss control. Never conditionally hidden based on scroll, session, or a cookie. It is chrome, not a notification.

---

## 10. The feedback widget — three placements, states only (no backend wiring)

Per `UX-and-Feedback-Spec.md` §5 / Decision C3. All three are built and verified in Field Notes:

1. **Under the recommendation card** (`1-field-notes-advisor.html`): "Was this useful?" → 👍/👎 buttons → conditional follow-up (👍 reveals a yes/no "did this change what you were going to use?"; 👎 reveals a one-line free-text box) → thanks state. States: idle → thumb-selected → follow-up-shown → thanks. Reusable verbatim on `/model/:id` if that route ever carries its own recommendation-shaped content; not required there by spec.
2. **On an expanded score cell** (`1-field-notes-results.html`, Quality lens only): the cell-expansion panel's own inline "Disagree with this score?" row — a dimension `<select>`, a score `<input type=number>`, a one-line reason `<input type=text>`, and a Submit that flips to a thanks line. States: idle → thanks.
3. **Footer** (`1-field-notes-results.html`, and — per spec — `/about`): "What should we measure next?" — two text inputs (model request, task request) → Send → thanks. States: idle → thanks.

**Implementation note for the build spoke:** every hidden/shown toggle here relies on the native `hidden` attribute. Any container element given its own `display` value in CSS (e.g. `.feedback-row{display:flex}`) **must** be paired with a `[hidden]{display:none !important}` rule (set once, globally, at the top of the stylesheet) — without it, a class-level `display:flex` beats the attribute selector's default `display:none` and the "hidden" element stays visible. This exact bug was caught and fixed during this build; don't reintroduce it.

---

## 11. Responsive behaviour

- **Advisor layout**: `grid-template-columns: 1.55fr 1fr` (primary card / side column) collapses to a single column under `860px`. Already implemented.
- **Methodology layout**: `220px` sticky TOC + content collapses to a single column, TOC becomes static (non-sticky), under `860px`. Already implemented.
- **Results matrix**: **not yet wrapped for narrow viewports** in the current mockup — this is a build-spoke TODO, not a re-decision. Wrap `table.matrix` in a `div` with `overflow-x:auto` so the table scrolls horizontally inside its own container below some threshold (recommend `~700px`) rather than the five-task-column table trying to reflow or the page itself gaining horizontal scroll. Do not redesign the table into a stacked/card layout for mobile — that would be a new component, and the matrix's whole value is the grid.
- **Base font-size**: 16–17px flat, no fluid/clamp scaling was used or is needed — the content is desktop-first (a benchmark reader on a laptop), and mobile is "must not break," not "must be optimised," consistent with `UX-and-Feedback-Spec.md` §6 ("mobile-optimised advisor beyond basic responsiveness" is explicitly out of v1 scope).
- **Feedback widgets**: the thumbs row, the dispute form row, and the footer form row are all `display:flex; flex-wrap:wrap` with `min-width` on their text inputs — they already degrade to stacked rows on narrow viewports without additional breakpoints.

---

## 12. Component inventory for the routes not designed

`/model/:id` and `/about` were explicitly out of scope for this design pass and are extrapolated by the build spoke from `UX-and-Feedback-Spec.md` §2. Every component they need already exists, built and verified, in the three designed screens — **no new visual component should be invented for either route:**

**For `/model/:id`** ("Per-model profile: scores, failure modes, latency, limits, verdict" — spec §2):
- The masthead + disclosure strip (shared chrome, exists on all three built pages).
- The **primary-card scaffold** from `1-field-notes-advisor.html` (`h2` model name, provider line, verdict blockquote) — repeat its **score block** (number + bar + band + caption, §6 above) once per task the model was scored on, instead of once for a single query.
- The **stat-row** three-up block (adversarial sub-score / p95 latency / run-to-run spread) from the same card, once per task.
- The **dimension-breakdown table** from the results-matrix cell-expand panel (§7) — this is exactly "the per-dimension breakdown" a model profile needs, already built and populated with real data patterns.
- The **rate-limit ceiling render** from the results-matrix ceiling lens (§7) — for a single model this simplifies to just showing that one model's row (either the constant-value treatment or the five-per-task-derived treatment, whichever applies).
- The **fallback-pairing box** from the advisor card, if the profile page states a suggested fallback independent of any specific query.
- Do **not** build a new "failure modes" component: the filter-table's fail-row pattern (`.frow` / `.freason`, monospace model id + reason text) already renders "a documented threshold this model fails," which is the model-profile equivalent of a failure mode when read model-first instead of query-first.

**For `/about`** ("why this exists, refresh cadence, changelog, how to contribute" — spec §2):
- Prose typography straight from `1-field-notes-methodology.html` (`h1`/`.lede`/`h2`/`p`, serif body, sans micro-labels) — no new type treatment needed for a prose-only page.
- The **footer feedback widget** (§10, placement 3) — spec explicitly places "what should we measure next?" on `/about` in addition to the Results footer; it is the same component, unchanged.
- A changelog is naturally a list of dated entries — reuse the `.limitation` block pattern from Methodology §2 (a bold lead line + a body paragraph + a bottom rule) rather than inventing a new list style.

No route gets a bespoke visual language. If a build-spoke engineer finds themselves designing a new card shape, table, or form control for either page, that's a sign to come back to this document rather than freelancing — the answer is almost certainly "reuse the thing that already exists."

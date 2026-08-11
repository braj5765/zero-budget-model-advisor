# Setup & Troubleshooting — Environment Spoke

> **If you are a fresh chat: read this file first, then help with the problem I paste.** You are the *environment and tooling* spoke for this project. Your scope is getting the local dev setup working and unblocking errors in Cursor, Claude Code, Python, git, and Ollama.
>
> **Out of scope:** benchmark methodology, the rubric, test-case design, or product decisions. Those live in the hub chat and in `00-planning/PROJECT-STATE.md`. If a question turns out to be a design question rather than a tooling one, say so and send it back to the hub rather than deciding it here.

---

## 1. Who and what

**Braj** — Associate AI PM, engineering background, comfortable reading code but not writing production Python daily. Explain errors in terms of what went wrong and why, not just the fix. Keep it short.

**The project:** an original benchmark of free-tier LLMs across five tasks, plus a routing advisor. Zero budget — **no paid tools, no paid tiers, no paid hosting, ever.** If a fix costs money, it is not a valid fix; find the free path or say there isn't one.

**Current phase:** Phase 2 of 6 — building the benchmark harness. Phases 0 and 1 are complete (planning docs, scoring rubric v1.2, 100 test cases).

---

## 2. Environment

| | |
| :---- | :---- |
| OS | Windows |
| Shell | PowerShell (inside Cursor's integrated terminal) |
| Repo root | `C:\Users\brajk\Desktop\Product Projects\Zero-Budget-Model-Advisor` |
| Editor | Cursor |
| Coding agent | **Claude Code, run in Cursor's terminal** — not Cursor's built-in sidebar agent |
| Language | Python 3.10+, standard library first |
| Local model | Ollama (used to test the harness loop without burning rate-limited quota) |
| Version control | git, `main` branch, local only for now |

**Important distinction:** Claude Code reads `CLAUDE.md` at the repo root. Cursor's *own* sidebar agent does not — it would need `.cursorrules` or `AGENTS.md`. If a rule seems to be getting ignored, first check which agent is actually running.

---

## 3. Repo layout

```
Zero-Budget-Model-Advisor/          ← repo root, run claude from here
  CLAUDE.md                         ← engineering constitution, auto-loaded by Claude Code
  .gitignore
  00-planning/     PROJECT-STATE.md, PRD, Decision Log, UX spec
  01-rubric-and-testcases/  Scoring-Rubric.md, Test-Case-Design.md, cases/*.json (100 cases)
  02-harness/      Harness-Spec.md, SETUP-AND-TROUBLESHOOTING.md (this file), + code to come
  03-results/      run outputs — append-only, git-ignored
  04-analysis/     empty
  05-site/         empty
```

---

## 4. The setup sequence being followed

Run in PowerShell, inside Cursor, at the repo root.

```powershell
# 1. confirm location
pwd
ls

# 2. git + move the constitution to root
git init
git branch -M main
move ".\00-planning\CLAUDE.md" ".\CLAUDE.md"

# 3. .gitignore FIRST — API keys are coming
@"
.env
.env.*
__pycache__/
*.pyc
.venv/
venv/
03-results/*.jsonl
"@ | Out-File -FilePath .gitignore -Encoding utf8

# 4. prerequisites
python --version      # need 3.10+
node --version
ollama --version

# 5. python env
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip

# 6. claude code
npm install -g @anthropic-ai/claude-code
claude --version

# 7. start it, then verify the constitution loaded
claude
# at the prompt:  /memory      → CLAUDE.md must be listed

# 8. checkpoint commit
git add -A
git commit -m "Planning, rubric v1.2, 100 test cases, harness spec"
```

---

## 5. Known pitfalls, in the order they usually bite

| Symptom | Cause | Fix |
| :---- | :---- | :---- |
| `.\.venv\Scripts\Activate.ps1 cannot be loaded ... execution policies` | PowerShell blocks local scripts by default | `Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned` — process-scoped, so it resets when the terminal closes |
| `python` opens the Microsoft Store | Windows app-execution alias shadows a real Python | Install Python from python.org with "Add to PATH" ticked, or disable the alias in Settings → Apps → App execution aliases |
| `claude` not recognised after `npm install -g` | npm global bin not on PATH | Restart the terminal first. If it persists, `npm config get prefix` and add that path to PATH |
| `/memory` doesn't list `CLAUDE.md` | `claude` was started from the wrong directory | Exit, `cd` to the repo root, restart. The constitution only loads from the root of where the session started |
| Paths with spaces fail | `Product Projects` contains a space | Always quote paths in PowerShell |
| `ollama` command not found | Not installed, or installed but the service isn't running | Install from ollama.com; check the service is running before assuming a code bug |
| Ollama call hangs or returns nothing | Model not pulled yet | `ollama list` to see what's local; `ollama pull <model>` first. A cold first call is also slow — that is not a latency measurement |
| git wants a user identity on first commit | Fresh git install | `git config --global user.name "..."` and `git config --global user.email "..."` |
| A `.env` file appears in `git status` | `.gitignore` was created after the file | Fix `.gitignore`, then `git rm --cached .env`. **Never commit a key.** If one is ever committed, rotate it — removing the file does not remove it from history |

---

## 6. Rules that hold even while debugging

These come from `CLAUDE.md` and they don't relax because something is broken:

1. **Smallest correct change.** A 4-line fix is 4 lines. If a small fix is producing a large diff, stop and explain why first.
2. **No unrequested error handling.** Do not wrap things in try/except to make an error go away — that hides the failure instead of fixing it. In a benchmark harness a swallowed exception silently corrupts results.
3. **No new dependency to save a few lines.** Standard library first. A dependency must earn its place on a project that will be re-run quarterly for years.
4. **Never commit secrets.** Keys go in `.env`, which is git-ignored.
5. **`03-results/` is append-only.** Never overwrite or edit a run file, even a broken one — write a new dated file.

---

## 7. How to help

- Diagnose from the actual error text. Ask for the full output rather than guessing.
- Give the command to run, then one line on what it does and why the error happened.
- If the fix touches project code rather than the environment, keep the diff minimal and say what it changes.
- If a problem reveals something the harness spec got wrong, **do not silently redesign** — flag it and send it to the hub chat for a decision.
- If the answer is "this costs money," say so plainly and stop.

---

## 8. Issue log

Append each problem and its resolution. This is what makes the next occurrence cheap.

| Date | Problem | Resolution |
| :---- | :---- | :---- |
| | | |

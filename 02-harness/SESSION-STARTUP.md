# Session Startup — Zero-Budget Model Advisor

> Quick reference for starting work each day. For first-time machine setup or troubleshooting a new error, see `SETUP-AND-TROUBLESHOOTING.md` in this same folder.

---

## One-time setup (already done, 2026-08-11)

These don't need repeating — noted here so it's clear what's already in place:

- Git installed (`git version 2.55.0.windows.3`), full Cursor restart was required before it was recognized in the integrated terminal
- `git init` + `git branch -M main` run at repo root
- `.gitignore` created (excludes `.env`, `__pycache__/`, `.venv/`, `03-results/*.jsonl`)
- Conda `base` environment carries Python 3.9.12 (too old — project needs 3.10+), so a dedicated conda environment **`zba`** was created with Python 3.11.15
- Project venv (`.venv`) created from inside `zba`, so it's seeded with Python 3.11
- Claude Code installed (`npm install -g @anthropic-ai/claude-code`) and authenticated (Claude Pro)

---

## Every time you open Cursor / a new terminal

Windows auto-activates conda's `base` environment in every new terminal, which has the wrong (too old) Python — so step 1 below is not optional, skipping it silently puts you back on Python 3.9.12.

```powershell
# 1. switch off base onto the project's Python 3.11 env
conda activate zba

# 2. confirm you're at the repo root (cd there if not)
cd "C:\Users\brajk\Desktop\Product Projects\Zero-Budget-Model-Advisor"

# 3. activate the project venv
.\.venv\Scripts\Activate.ps1

# 4. sanity check — should show Python 3.11.x
python --version

# 5. start Claude Code
claude
```

Once at the `claude` prompt, run `/memory` to confirm `CLAUDE.md` loaded (it should open the file — that's the confirmation, not an error). If it doesn't show up, you weren't at the repo root when `claude` started: `/exit`, `cd` back to the repo root, restart `claude`.

If step 3 is blocked by a PowerShell execution-policy error:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
```
(Process-scoped — resets automatically when the terminal closes, so this is safe to re-run each time it comes up rather than a permanent system change.)

---

## Known gotchas

| Symptom | Cause | Fix |
| :---- | :---- | :---- |
| `python --version` shows 3.9.12 | Landed in conda `base`, not `zba` | `conda activate zba` |
| `git`/`claude`/other newly-installed tool "not recognized" right after installing it | Cursor cached its environment/PATH at launch | Fully quit Cursor (check it's not still running in the tray/Task Manager) and reopen — a new terminal *tab* alone isn't enough |
| Command errors with `Unexpected token` mentioning `(base)` or `(zba)` | The shell prompt text got pasted in front of the actual command | Re-run just the command itself, without the `(env) PS C:\...>` prefix |

---

## Then continue with

Prerequisites already confirmed: Node `v22.14.0` ✔. Ollama not yet installed (free, from ollama.com — needed for the local dry-run, not blocking to start).

Remaining one-time step: checkpoint commit (`git add -A` + `git commit -m "..."`) before pasting the first build prompt. See `SETUP-AND-TROUBLESHOOTING.md` for the full sequence and pitfall table.

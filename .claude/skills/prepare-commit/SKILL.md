---
name: prepare-commit
description: Prepare a commit in Zuza's Manager – check the diff contains exactly one feature, run the quality gate, summarize, propose the message and wait for the developer's approval. Use when a piece of work is done or the developer asks to commit.
---

# Prepare a commit

Commit rules are in `AGENTS.md` → Git; the project hook enforces them. Steps:

1. `git status` and `git diff --stat` – exactly **one feature**. If the change mixes features, propose a split.
2. Nothing unwanted included: `.env`, `*.sqlite3`, `.verify/`, `staticfiles/`, scratch files.
3. `make check` passes.
4. Summary for the developer (Czech, short): what changed, how it was verified, what was **not** verified, decisions taken on the way.
5. Proposed message: short English imperative summary (e.g. "Add shift schedule week view"), optional body with the why.
6. **Wait for explicit approval.**
7. Stage with `git add <files>` as its own command, then run `git commit -m "…"` alone (why: `AGENTS.md` → Skills and hooks). Unrelated work in progress has to be moved away first – ask the developer how.

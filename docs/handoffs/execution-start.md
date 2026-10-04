# Execution startup

Date: 2026-10-04 (Europe/Paris).

## Authority and ownership

[The active goal](../goal.md) was copied verbatim from the user's second pasted file. It replaces the earlier charter. The full backend project remains the active objective; saving this context does not complete it.

The default execution owner is GPT-5.6 Sol at `xhigh`. GPT-6 Astra at `xhigh` owns the four designated gates. Do not start the small MLX kernel before Gate A is complete and a return to Sol has occurred.

## Verified state

- Git repository initialized on `main`; preparation commit `0d9bd07` contains the earlier context and working rules.
- The working folder was clean before saving the active specification.
- Session metadata for the current turn reports `model: gpt-6.1-sol`, `effort: xhigh`. This does not match the requested default model.
- Computer Use refused access to the Codex app with: `Computer Use is not allowed to use the app 'com.openai.codex' for safety reasons.` No model was changed.
- The available chat tools do not expose a current-chat model setter. Tools for creating or messaging other chats are not a verified model switch for this running turn.
- Machine architecture: `arm64`.
- macOS: `15.3.1`, build `24D70`.
- `uv` is available at `/opt/homebrew/bin/uv`.
- `gh` is available at `/opt/homebrew/bin/gh`.
- No Git remote is configured. Commits cannot be pushed until a destination is supplied.
- `git ls-remote https://github.com/eonsystemspbc/fly-brain.git HEAD refs/heads/main` reported `a3db62f9436074e485c0278290c2164ed6150808` for both references. This is an observation, not a local pin or imported source. Revalidate before choosing the baseline commit.

## Commands and checks

Startup inspection used:

```sh
git status --short --branch
git log -3 --oneline
cat AGENTS.md
cat README.md
rg --files -g '!.git'
uname -m
sw_vers
command -v uv
command -v gh
git remote -v
git ls-remote https://github.com/eonsystemspbc/fly-brain.git HEAD refs/heads/main
```

The current turn's `model` and `effort` were read from its `turn_context` in the local session log, without modifying session state.

Documentation checks before committing startup context:

- Byte-for-byte comparison of `docs/goal.md` with the user-supplied attachment.
- Existence checks for local Markdown links in `README.md`, `docs/project-charter.md`, and this handoff document.
- `git diff --cached --check`.
- Final `git status --short --branch`.

No numerical tests have been run. No application code or dependencies have been added. No database content has been created or deleted.

## Next required step

Select GPT-5.6 Sol at `xhigh` for this chat and resume the active goal. Do not substitute GPT-6.1 Sol without the user's explicit change to model ownership.

Under the requested model, complete Milestone 0 exactly as specified: pin and inspect upstream, run the smallest Brian2 central processing unit (CPU) experiment, collect numerical and backend-contract evidence, record licensing, and write `docs/mlx-port-baseline.md`.

Collect disagreements without adjudicating them. Commit the completed reference work, write `docs/handoffs/astra-numerical-contract.md`, then emit the exact Gate A handoff request and stop for GPT-6 Astra.

No success criterion for the backend is yet verified. The goal remains incomplete.

# Former repository delegation skill

Historical record only. This snapshot does not govern current work. The installed
`bounded-subagent` skill in the session catalog owns reusable delegation
procedures; current project model and review choices belong to `AGENTS.md`.

Archived without changing the original skill or interface text from source
`e8d2919cb277ae2512c102dbac325290957b1bfa`. Earlier review briefs and checkpoint
links refer to this snapshot. Its former repository paths were `skills/bounded-subagent/SKILL.md`
and `skills/bounded-subagent/agents/openai.yaml`.

## Original skill

---
name: bounded-subagent
description: Delegate a bounded component using the model and reasoning effort specified by the user or project, await completion, verify evidence, and integrate the result. Use for authorized reviews, investigations, or explicitly delegated implementation; keep existing assignments with their current owners.
---

# Bounded Subagent

Keep the parent agent's model and reasoning effort unchanged. Delegate one component with its own authorized settings, then resume the parent's work after inspecting the result.

## Scope and ownership

Use for a bounded review, investigation, or explicitly delegated implementation component. Keep routine work with the parent unless delegation is requested or useful and authorized. Honor the user's scope and applicable project instructions. This skill does not authorize schema changes, database deletion, publishing, or other actions requiring separate approval.

Keep an already assigned manual review with its current owner. Do not duplicate it, interrupt it, or overwrite its files. Future reviews can use this workflow when the user or project instructions authorize delegation.

## Resolve the model and effort

Resolve `model` and `reasoning_effort` independently from the latest user instructions and applicable project rules. Preserve the exact choices; verify that the available collaboration tool supports the requested pair. Do not hard-code a model catalogue or assume every model supports the same levels.

If either value is missing and no applicable user or project default supplies it, ask for the missing choice before dispatch. If the user expressly requests inheritance of both parent settings, omit both overrides. Never silently substitute a model, change the effort, or let an omitted effort select an unintended default.

The parent's reasoning level does not itself authorize delegation or select the child's settings. Record the resolved pair in the assignment.

## Prepare the assignment

Read the current project plan and relevant evidence. Give the child a self-contained assignment containing:

- One bounded question or component, the requested deliverable, and the condition for finishing.
- The workspace's absolute path, repository checkpoint where applicable, relevant working-tree changes, and existing owners of concurrent work.
- Applicable instruction files, the authoritative plan, contract, evidence paths, exact reproduction commands, and unresolved disagreements.
- Required invariants, acceptance criteria, and known limitations. Distinguish observed facts from hypotheses.
- The permitted actions and file scope. Default reviews to read-only; explicitly assign any diagnostic or implementation edits and verification.

The child should return a decision or a precise unresolved blocker, supporting measurements or source locations, material limitations, and the exact next action for the parent. Tell it to stop when this component is resolved, without continuing the larger project or requesting a parent-model switch.

## Spawn with the resolved settings

Call `collaboration.spawn_agent` directly with a descriptive `task_name`, the complete assignment in `message`, and `fork_turns: "none"`. Pass the resolved model as `model` and level as `reasoning_effort` explicitly, except when inheritance of both was expressly requested. Fresh context permits model and effort overrides without copying the parent's full history.

If the requested pair is unsupported or dispatch fails, report the limitation and leave dependent work unresolved. Do not fall back to another model or effort.

Use the collaboration tools directly; they are not available inside `functions.exec`. Do not create a separate user-owned chat through `create_thread` for this subtask. Use `collaboration.send_message` for new evidence during an active assignment and `collaboration.followup_task` for a bounded correction after completion. Do not authorize nested delegation unless the assignment requires it and the user or project instructions allow it.

## Await and integrate

Record the child's identifier and assignment. Continue only independent work while it runs. Await completion using `collaboration.wait_agent`, with waits of at most 60 seconds and useful progress updates during longer work. This tool returns an update summary; the completed review arrives separately as the child's final message. Inspect that final result; a timeout, progress message, or successful spawn is not a completed review.

Parent and child share the filesystem. Serialize edits to shared files and keep the parent responsible for integration, commits, and pushes unless explicitly assigned otherwise. A read-only child must not edit project files, commit, push, or change project rules.

Inspect any changed files and the cited evidence. Reproduce the checks needed to support the decision before accepting it. If the evidence is incomplete or contradicts the contract, give the same child a bounded follow-up instead of silently broadening the task or treating its conclusion as approval.

Record accepted decisions, verification, unresolved issues, and the next step in the project's authoritative progress record when one exists. State skipped checks and material limitations explicitly. Resume dependent implementation only when the component's acceptance criteria are met; a review that exposes a blocker leaves the dependent work blocked.

## Original interface metadata

```yaml
interface:
  display_name: "Bounded Subagent"
  short_description: "Delegate with your chosen model and reasoning effort"
  default_prompt: "Use $bounded-subagent to delegate this component with the model and reasoning effort specified in my instructions, then await and verify the result."
```

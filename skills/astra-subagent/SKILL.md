---
name: astra-subagent
description: Delegate a bounded scientific, numerical-correctness, or difficult kernel-design judgment to GPT-6 Astra at xhigh, await its evidence, and integrate the result. Use when deeper review is needed and delegation is authorized; leave ordinary implementation and already assigned manual reviews with their current owners.
---

# Astra Subagent

Keep the parent agent's model and reasoning effort unchanged. Delegate the component that needs deeper judgment, then resume the parent's work after inspecting the result.

## Scope and ownership

Use for scientific interpretation, numerical acceptance, difficult kernel design, or a requested final scientific review. Do not delegate routine implementation solely because it touches numerical code. Honor the user's scope and applicable project instructions. This skill does not authorize schema changes, database deletion, publishing, or other actions requiring separate approval.

Keep an already assigned manual review with its current owner. Do not duplicate it, interrupt it, or overwrite its files. Future reviews can use this workflow when the user or project instructions authorize delegation.

## Prepare the assignment

Read the current project plan and relevant evidence. Give the child a self-contained assignment containing:

- One bounded question or component, the requested deliverable, and the condition for finishing.
- The repository's absolute path, branch and commit checkpoint, relevant working-tree changes, and existing owners of concurrent work.
- Applicable instruction files, the authoritative plan, contract, evidence paths, exact reproduction commands, and unresolved disagreements.
- Required invariants and acceptance criteria, including any known numerical limitations. Distinguish observed facts from hypotheses.
- The permitted actions and file scope. Default to read-only review; explicitly assign any necessary diagnostic edits and verification.

The child should return a decision or a precise unresolved blocker, supporting measurements or source locations, material limitations, and the exact next action for the parent. Tell it to stop when this component is resolved, without continuing the larger project or requesting a parent-model switch.

## Spawn Astra explicitly

Call `collaboration.spawn_agent` directly with a descriptive `task_name`, the complete assignment in `message`, and all three settings:

```json
{
  "model": "gpt-6-astra",
  "reasoning_effort": "xhigh",
  "fork_turns": "none"
}
```

These explicit settings are essential: Astra uses `xhigh` even when the parent uses `max`. Do not substitute another model or inherit the parent's reasoning effort. If Astra cannot be spawned with these settings, report the limitation and leave work dependent on its review unresolved.

Use the collaboration tools directly; they are not available inside `functions.exec`. Do not create a separate user-owned chat through `create_thread` for this subtask. Use `collaboration.send_message` for new evidence during an active assignment and `collaboration.followup_task` for a bounded correction after completion. Do not authorize nested delegation unless the assignment requires it and the user or project instructions allow it.

## Await and integrate

Record the child's identifier and assignment. Continue only independent work while it runs. Await completion using `collaboration.wait_agent`, with waits of at most 60 seconds and useful progress updates during longer work. This tool returns an update summary; the completed review arrives separately as the child's final message. Inspect that final result; a timeout, progress message, or successful spawn is not a completed review.

Parent and child share the filesystem. Serialize edits to shared files and keep the parent responsible for integration, commits, and pushes unless explicitly assigned otherwise. A read-only child must not edit project files, commit, push, or change project rules.

Inspect any changed files and the cited evidence. Reproduce the checks needed to support the decision before accepting it. If the evidence is incomplete or contradicts the contract, give the same child a bounded follow-up instead of silently broadening the task or treating its conclusion as approval.

Record accepted decisions, verification, unresolved issues, and the next step in the project's authoritative progress record. State skipped checks and scientific limitations explicitly. Resume the parent's implementation only when the component's acceptance criteria are met; a review that exposes a blocker leaves the dependent work blocked.

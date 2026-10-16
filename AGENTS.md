# fly-brain project instructions

## Active Project Specification

Read [milestone.md](milestone.md) before project work. It owns the plan,
current holds, acceptance criteria, progress, unresolved issues, and completion
evidence. Keep it updated after significant work.

Keep all repository documentation within 10,000 whitespace-delimited words
combined. The input gate counts tracked Markdown, reStructuredText, AsciiDoc,
plain-text and LaTeX documents. License texts and generated execution data are
separate. Keep current rules and bounded evidence; use Git for detailed history.

Use the [agent documentation index](docs/agent/README.md) to find each document's
owner. The [development guide](docs/agent/development.md) defines the required
streamlined workflow: complete diagnosable implementation batches, then run the
minimum necessary validation. Keep one implementation and one owner per rule;
read only the material needed for the current outcome.

Preserve the FlyWire v783 leaky integrate-and-fire model and the
[reviewed numerical contract](docs/agent/numerical-contract.md), including pinned
inputs, reference behavior, experiment definitions, and spike output contracts.
Keep all scientific acceptance gates; changed arithmetic or execution modes
require their recorded qualification before adoption.

Keep the application MLX-only on Apple silicon, managed by uv. Exclude Conda,
NVIDIA backends, and non-essential dependencies. Brian2 and PyTorch are
qualification-only references, never production backends.
Keep the application database-free.

Apply the [project architecture policy](docs/agent/architecture-policy.md).
Use rules where they protect actual behavior or maintainability. Concrete MLX
backend types and framework-specific scientific references are permitted.
Preserve the practical architecture, useful boundaries and scientific gates.

Preserve source, pinned model inputs, authored scientific rules and incoming
work. Write runs to fresh output directories. Current holds and their releases
belong in `milestone.md`.
Only disposable diagnostics belong in ignored `logs/`, which successful
commit/push hooks clear. Preserve legacy `.quality-reports/` until classified.
Store reusable scientific
evidence, inputs, native arrays, provenance, verification reports and unresolved
failure diagnostics in ignored `executions/`; hooks never delete that directory,
even without a retention entry. Repeated failures get fresh report directories.
Reusable quality caches also live there. The retention manifest records current
consumers, release conditions and legacy diagnostic holds; removing an entry does
not delete evidence. Delete retained evidence only after explicitly confirming
that its repeat, batch, scoring, review and reuse consumers are finished.
Keep the seven registered independent regression fixtures while their consumers
need them. Historical conclusions do not imply that deleted raw proofs remain
reproducible from this checkout. Use bounded diagnostic summaries with explicit
omissions. Generated outputs do not belong in Git. Edit directly without
temporary preservation or backup copies.

## Non-production schema and database authorization

This is a non-production project. The user grants standing authorization for
schema and database changes within the authorized task, including migrations,
data updates/deletions, resets, and automated temporary, test, and CI database
cleanup. Do not seek separate permission for these operations. This local
instruction overrides general schema and database approval requirements.

## Implementation and scientific review

Use GPT-6.1 Sol for implementation at the user-selected effort (currently
`xhigh`). Only the user may change the parent model.

Resolve engineering, precision, representation and causal decisions here using
verified evidence. Agent-authored implementation notes do not create human
approval requirements. Use Astra
only when something is broken and we cannot resolve it ourselves after diagnosis
and repair attempts. State the concrete failure, attempted fixes and remaining
blocker before dispatch. Routine reviews and design decisions stay here. For a
necessary escalation, use `bounded-subagent`, `gpt-6-astra` at `xhigh`, fresh
context, one reviewer at a time and no implementation delegation. Await
completion, verify the evidence and record the decision and limits. Keep assigned
reviews with their current owners.

## Repository remotes

Push project commits to the user-owned `origin`:
`git@github.com:PraxisMechanica/fly-brain-mlx.git`.
Use `upstream` only as the public reference repository.

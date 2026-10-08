# fly-brain project instructions

## Active Project Specification

Read [milestone.md](milestone.md) before project work. It owns the plan,
current holds, acceptance criteria, progress, unresolved issues, and completion
evidence. Follow its latest user amendments over historical checkpoints and
keep it updated after significant work.

Use the [agent documentation index](docs/agent/README.md) to find detailed
contracts, review records, and historical evidence.

Preserve the FlyWire v783 leaky integrate-and-fire model and the
[reviewed numerical contract](docs/agent/numerical-contract.md), including pinned
inputs, reference behavior, experiment definitions, and spike output contracts.
Keep all scientific acceptance gates; changed arithmetic or execution modes
require their recorded qualification before adoption.

Keep the application MLX-only on Apple silicon, managed by uv. Exclude Conda,
NVIDIA backends, and non-essential dependencies. Brian2 and PyTorch are
qualification-only references, never production backends.
Keep the application database-free.

Preserve data, scientific evidence, and incoming work. Write new runs to fresh
output directories. Current development holds and their releases belong in
`milestone.md`.
Store disposable developer diagnostics under ignored `logs/`; successful commit
and push hooks remove that folder after all checks finish. Failed checks retain
their diagnostics. Store complete scientific run bundles under ignored
`executions/`, with fresh directories and the required evidence intact. Keep
numerical fixtures, scientific manifests, and reviewed decisions; execution
evidence is excluded from automatic log cleanup. Use compact diagnostic summaries
with explicit omission counts and artifact locations. Generated outputs do not
belong in Git. Edit files directly without temporary preservation or backup
copies; overwrite disposable diagnostic outputs as needed.

## Non-production schema and database authorization

This is a non-production project. The user grants standing authorization for
schema and database changes within the authorized task, including migrations,
data updates/deletions, resets, and automated temporary, test, and CI database
cleanup. Do not seek separate permission for these operations. This local
instruction overrides general schema and database approval requirements.

## Implementation and scientific review

Use GPT-6.1 Sol for implementation at the user-selected effort (currently
`xhigh`). Only the user may change the parent model.

Resolve precision, numerical representation, and implementation choices using
the delegated engineering judgment. For deeper scientific, numerical, or
kernel-design judgment, use the installed `bounded-subagent` skill.
Spawn `gpt-6-astra` explicitly at `xhigh` with fresh context; await completion,
verify the evidence, and record the decision and limits before dependent work.
Sol then resumes implementation. Keep assigned reviews with their current
owners; future reviews use this workflow instead of historical manual switches.

## Repository remotes

Push project commits to the user-owned `origin`:
`git@github.com:PraxisMechanica/fly-brain-mlx.git`.
Use `upstream` only as the public reference repository.

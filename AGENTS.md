# fly-brain project instructions

## Active Project Specification

Read [milestone.md](milestone.md) before project work. It owns the plan,
current holds, acceptance criteria, progress, unresolved issues, and completion
evidence. Follow its latest user amendments over historical checkpoints and
keep it updated after significant work.

Preserve the FlyWire v783 leaky integrate-and-fire model and the
[reviewed numerical contract](docs/mlx-port-baseline.md), including pinned
inputs, reference behavior, experiment definitions, and spike output contracts.
Keep all scientific acceptance gates; changed arithmetic or execution modes
require their recorded qualification before adoption.

Keep the application MLX-only on Apple silicon, managed by uv. Exclude Conda,
NVIDIA backends, and non-essential dependencies. Brian2 and PyTorch are
qualification-only references, never production backends.

Preserve data, scientific evidence, and incoming work. Write new runs to fresh
output directories. Current development holds and their releases belong in
`milestone.md`.

## Implementation and scientific review

Use GPT-6.1 Sol for implementation at the user-selected effort (currently
`xhigh`). Only the user may change the parent model.

Resolve precision, numerical representation, and implementation choices using
the delegated engineering judgment. For deeper scientific, numerical, or
kernel-design judgment, use [the bounded subagent skill](skills/bounded-subagent/SKILL.md).
Spawn `gpt-6-astra` explicitly at `xhigh` with fresh context; await completion,
verify the evidence, and record the decision and limits before dependent work.
Sol then resumes implementation. Keep assigned reviews with their current
owners; future reviews use this workflow instead of historical manual switches.

## Repository remotes

Push project commits to the user-owned `origin`:
`git@github.com:PraxisMechanica/fly-brain-mlx.git`.
Use `upstream` only as the public reference repository.

# fly-brain project instructions

## Active Project Specification

Read [milestone.md](milestone.md) before project work. It owns the plan,
current holds, acceptance criteria, progress, unresolved issues, and completion
evidence. Follow its latest user amendments over historical checkpoints and
keep it updated after significant work.

Keep all repository documentation within 10,000 whitespace-delimited words
combined. The input gate counts tracked Markdown, reStructuredText, AsciiDoc,
plain-text and LaTeX documents. License texts and generated execution data are
separate. Keep current rules and bounded evidence; use Git for detailed history.

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

Apply the [project architecture policy](docs/agent/architecture-policy.md).
The user's 2026-10-14 amendment supersedes the generic strict architecture
profile: use rules only where they protect this application's actual behavior
or maintainability. Concrete MLX backend types and framework-specific scientific
references are permitted. Do not introduce portable tensor abstractions or make
completion depend on a general 37-rule analyzer. Preserve useful existing
boundaries, scientific gates and automatic affected-test checks.

Preserve source, pinned model inputs, authored scientific rules and incoming
work. Write runs to fresh output directories. Current holds and their releases
belong in `milestone.md`.
Generated outputs are deleted by default at commit and push boundaries. Store
diagnostics under ignored `logs/` and execution working data under ignored
`executions/`. Before an output must cross a commit, register its exact path,
current operational reason and release condition in
`tools/code_quality/retention.json`. Scientific output is not an automatic
exception. Complete required verification before deletion, or register the
unfinished verification consumer explicitly. Failed hooks retain diagnostics
until that failure is resolved; a successful commit requires an explicit
exception for any remaining output. Remove exceptions when their consumer ends.
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

# Parallel refactor assignments — 2026-10-06

The user explicitly requested bounded parallel work and committed handoffs.
Decision confidence: 97% at 0a313d02b56d886542d130134346506106a5f926.
All three implementation agents inherit GPT-6.1 Sol at xhigh.

Each worker uses an independent local-main clone pinned to that commit. The
clones share installed dependencies read-only, have separate Git metadata and
pre-commit caches, and retain their source/evidence. No feature branch or
competing origin/main push is created. The parent integrates and pushes serially.

| Agent | Component | Exclusive file scope |
| --- | --- | --- |
| architecture_ownership | Reviewed owners/roles, binding fingerprints, resources/public exports and typed metadata loader | New tools/architecture/policy.py, compact ownership metadata, its dedicated test, ownership evidence and optional architecture-ownership.md |
| architecture_symbols | Native symbol/type-definition/call relationships, alias handling and graph primitives | New symbols/graph modules and dedicated tests; compiler.py/compiler tests only if needed; symbol evidence |
| composition_refactor | Separate bootstrap assembly from owned runtime use cases; preserve lazy imports, configuration, load/clock boundaries and CLI behavior | bootstrap.py, cli.py; owned module/ports/commands/input-service wiring; qualification/service.py if needed; neutral qualification ports; composition/package tests and the narrow test_parity_options.py seam update; composition evidence |

The parent exclusively owns shared pyproject/justfile/hook/workflow configuration,
AGENTS.md, milestone.md, quality-coverage.md, the agent index, integration and the
current comparison rule repair. No worker edits another worker's files. Workers
request a parent allocation before expanding file scope.

Ownership metadata and native semantic IR have no unpublished API dependency:
metadata uses the existing inventory records; native IR emits explicit locations
and generic graph relationships. The parent joins them and implements the full
rule/gate integration. Composition changes application declarations; reconcile
its final committed symbols and public contracts into the ownership registry
at integration. Do not guess future declarations or register broad exemptions.

Each worker must install required hooks, run focused checks plus the existing
shared gate, and commit coherent verified changes before handoff. It returns
SHAs, exact files, actual commands/results, coverage limits, and integration
requirements. No hook bypass, dependency installation, push, rebase, branch
creation, scientific mode change or full-matrix execution is assigned.

The parent reviews each committed diff and evidence, imports the commit without
bypassing mandatory commit checks, reconciles shared metadata/configuration,
checks the combined snapshot, and pushes to origin/main in sequence. Native
resolution limits and missing applicable mechanisms remain COV002; green
component checks do not establish all 37 rules or new scientific acceptance.

## Committed handoffs and follow-ups

At parent `471ab69`, composition worker commit `05dd220` is integrated and pushed
with both hooks and 150 parent behavior/boundary cases passing. Native resolver
worker commit `ffbc2fe` passes 84 parent source fixtures and is being integrated.
Ownership worker commit `d6e8d43` remains preserved for the next serial join.

Decision confidence for the two independent follow-ups: 93%. Implementation
settings remain inherited GPT-6.1 Sol at xhigh; the accepted scientific review
remains with its existing fresh-context GPT-6 Astra reviewer.

| Owner | Bounded follow-up | Exclusive scope and finishing condition |
| --- | --- | --- |
| architecture_symbols | Export actual structured native Pyright types | New native_types Python/JS bridge, its dedicated fixtures and compact evidence; preserve the committed resolver files. Verify native categories/signatures/generic identities and fail closed on unsupported data; commit before handoff. |
| composition_refactor | Opaque native sessions and independent qualification expectations | Neutral simulation observations/session provider and qualification ports/observer/ledger/paired/case/batch callers plus dedicated tests/evidence. Preserve engine arithmetic, reference/build sources, bootstrap/CLI and other domains. Complete the accepted transparency/integrity and shortest pinned-run adoption qualification; commit checked slices before handoff. |

The exact session assignment is retained in the worker conversation. Additional
caller allocation comes from the parent before an edit. No worker changes
shared configuration, policy metadata, status/index documents, dependencies,
other workers' code, branches or remote refs. The parent reconciles final
committed declarations after application and analyzer integration. The native
structured-type component and opaque observation boundary do not touch each
other's files; their checks and parent policy joins are serialized.

# MLX fly-brain milestones

Audience: agents. Updated 2026-10-14 (America/Los_Angeles).
Project policy is in [AGENTS.md](AGENTS.md); the
[architecture policy](docs/agent/architecture-policy.md) owns the practical rule
review. The [numerical contract](docs/agent/numerical-contract.md) owns scientific
acceptance, and [developer workflow](docs/agent/development.md) owns commands.

## Current task and latest user amendment

Finish rearchitecture/refactor and cleanup for handoff to the prior implementation
agent. The user's latest amendment rejects architecture whose complexity outweighs
the application. Concrete backend dependencies are acceptable: production remains
MLX-only. Assess each rule for this project instead of following the generic
strict profile blindly. Decision confidence: 99%, reviewed at `5249fc5`.

This amendment supersedes the former requirement to finish all 37 strict predicates
and the architecture hold tied to that analyzer. Completing runtime call-target,
alias/effect/control-flow analysis, portable numerical values and provider-neutral
model execution is outside this refactor. Retained experimental tools are not a
required development roadmap, and their missing capabilities are not project
completion blockers. Do not claim those tools provide complete analysis.

The current change records the per-rule assessment and reconciles active agent
documents. It changes no application code, numerical behavior, scientific gates,
source identity guards, import contracts or automatic test selection.

## Bounded completion criteria

- Keep simulation, qualification and comparison responsibilities understandable;
  retain useful boundaries and remove duplication only when it has an actual
  maintenance cost. Do not add role layers or interfaces to satisfy a catalog.
- Address demonstrated correctness or maintenance problems found in the existing
  components. A concrete MLX type, legitimate framework inheritance, array index,
  or incomplete experimental static proof is not by itself such a problem.
- Preserve the pinned model inputs, reference lineage, five protected source
  identities, seven regression fixtures, scientific behavior and output contracts.
- Verify actual changes through existing automatic affected checks and tests;
  deliver small commits to `origin/main`, leave a clean tree, and provide a concise
  handoff with scientific implementation still outstanding.

New simulator features, numerical remedies, complete scientific qualification and
performance work remain outside this refactor agent's scope.

## Delivered cleanup and verification

The tool/test cleanup is delivered through `5249fc5` on `origin/main`. Its
[verification records](docs/agent/refactor-evidence.md) include failed attempts,
repairs, exact hosted results and timing limits. Delivered components include
injected observations and external facts, immutable causal-audit values, typed
reference digests and selected identifiers, pure reference parameters, scoped
ownership/import/type checks, metric calculation reuse, and separate human/agent
documentation.

The latest workflow avoids repeated tests:

- Commit and continuous integration (CI) each run one affected-test invocation.
  Agents do not add manual pytest runs; push/manual stages do not run tests.
- Adopt checked worker descendants by fast-forward, without a second integration
  commit that repeats local tests. Only the parent pushes shared project delivery.
- Static checks evaluate changed sources and affected dependents. Existing
  calculations are reused with input/tool identity invalidation.
- Broad checker simulations and guard-weakening exercises are excluded from
  routine application runs. Focus verification on actual changed behavior.
- CQ001/CQ002/CQ003 numerical metrics are advisory. No 0.01-point ratchet or
  mandatory score improvement applies. Actual check failures still block.

The final code-change hosted check passed 177 selected tests, with 9 deselected,
in 74.13 seconds; this is not a full application-suite benchmark. The final
handoff-only hosted check passed without replaying application tests. No scientific
qualification was run for that tool cleanup.

Historical records and generated output archives were removed under the user's
output policy. Seven independent fixtures remain under `tests/data/reference`,
totaling 45,360 bytes. Five protected sources preserve the adapted Brian2/Torch
references, extracted parameter factory and two legacy MLX observation oracles.
Pinned FlyWire inputs and licences remain intact. Import and metric-fact caches
have explicit operational consumers in the retention manifest; completed
scientific/timing outputs have no continuing exception.

## Disposition of the former six findings

The [architecture policy](docs/agent/architecture-policy.md) records the decision
for each catalog rule and the relevant source scopes. The former `Advance`
implementation-type finding is accepted for the private MLX backend. Framework
model definitions in qualification references are permitted; no portability-driven
Torch/Brian separation is required. The four identifier records describe partial
branding and unproved conversion origins, not demonstrated incorrect calculations.
Use typed identities where they prevent actual confusion; ordinary array positions
remain numeric coordinates. Apply review and affected tests to real mapping changes.

The unchanged strict registry still contains those historical observations and
capability limits. Its source hashes and inventory guards remain useful; its
strict findings are not the acceptance standard for this project. The
[coverage record](docs/agent/quality-coverage.md) distinguishes required checks,
review guidance and experimental mechanisms.

## Remaining handoff work

The project-rule reassessment and its bounded handoff are recorded in the current
agent documents. The three read-only component reviews established no additional
application defect behind the former six findings. Delivery uses the existing
mandatory commit/push checks; no runtime tests are needed for these document-only
changes. Any subsequent source cleanup must identify a concrete problem,
its affected callers, the smallest repair and meaningful verification before
implementation. Do not resume the generalized analyzer or tensor-contract program.
The prior implementation agent can continue scientific work under the unchanged
numerical contract; there is no prerequisite to finish the retired analyzer plan.

The complete 52-case scientific matrix and prescribed sugar/P9 four-trial
comparisons remain unfinished. Removed historical records do not establish current
source or execution-mode acceptance. Fresh qualification must satisfy all existing
scientific gates before its working outputs expire. No scientific acceptance or new
execution mode is approved by the architecture amendment.

## Checkout and ownership

Use current `origin/main`. The delivery checkout is
`/Users/ocasta/.codex/worktrees/pr-split/fly-brain`; the original
`/Users/ocasta/Code/fly-brain` remains an unchanged detached historical checkout.
The parent owns shared policy, documents, retention and serial integration.
Existing worker assignments retain their owners; committed components must be
verified before adoption. No message has been sent to the implementation chat.

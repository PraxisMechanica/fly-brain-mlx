# MLX fly-brain milestones

Audience: agents. Updated 2026-10-14 (America/Los_Angeles).
Project policy is in [AGENTS.md](AGENTS.md); the
[architecture policy](docs/agent/architecture-policy.md) owns the practical rule
review. The [numerical contract](docs/agent/numerical-contract.md) owns scientific
acceptance, and [developer workflow](docs/agent/development.md) owns commands.

## Current task and latest user amendment

The user's 2026-10-14 implementation instruction supersedes the completed
refactor-only scope below. Continue from `9f89ef6` on current `origin/main` in
`/Users/ocasta/.codex/worktrees/pr-split/fly-brain` until the pinned model has a
scientifically qualified end-to-end MLX implementation. Work in this chat only;
the newer explicit single-thread instruction overrides standing delegation and
scientific-subagent procedures. Preserve the practical architecture, protected
references, pinned inputs, numerical tolerances and every acceptance gate.
Decision confidence: 99%, inspected at `9f89ef6` (clean and equal to fetched
`origin/main`). No new arithmetic or execution mode is accepted by this amendment.

The user's later 2026-10-14 amendment requires **less than 10% of working time
spent waiting for tests**. Implementation comes first; automatic affected hooks
and CI own routine testing. Do not launch another broad scientific suite for a
fixture, reporting or provenance repair. Rerun a failed scientific check directly;
repeat expensive proofs only when their numerical/observation dependencies change
or required evidence is absent. Run the mandatory matrix on stable implementation,
with useful independent work during execution. Count idle scientific, hook and CI
waiting toward the target; background execution counts as productive overlap only
while actual independent work advances. The target has not yet been demonstrated,
and does not waive scientific gates. Decision confidence: 99% at `e519de7`.

The user's subsequent amendment sets a **five-minute maximum for test runs** and
requires careful diagnosis of any overrun. No long run is active. Full-matrix
launch is held while the parent diagnoses the preservation harness with bounded
pinned workloads (32 steps/four trials, external 120-second timeout). Preserve
all native/discrete/state gates; do not reduce scientific case coverage or relabel
long tests to evade the limit. Decision confidence: 95% at `c4556ce`.

Bounded profiling completed in 47.861 seconds for 32 steps/four trials, including
profiling, construction and proof writing. It found strided full-edge due-mask
checks, repeated contiguous copies for queue hashing, and default-level ZIP
compression. Commit `b626b4c` gathers each trial's expected due mask in
contiguous order, hashes native queue slots directly in the same canonical order,
and writes the same lossless NPZ arrays at ZIP level 1. The identical workload
then took 36.262 seconds (24.23% less). All 142 saved arrays, all four trial
receipts and every one of the 30 gates compare exactly. The earlier verifier's
scalar byte-view error was repaired without rerunning either profile.

Immutable pinned graph/history buffers are now reused, and the native comparator
retains validated device maps until different immutable maps are supplied. The
same profile then took **34.308 seconds** (28.32% less than the original). All 142
native arrays and all four trial receipts still match the original exactly.
All **66 affected native transparency, fault, slot, chunk, repeat, batch and
artifact checks passed in 14.41 seconds**, with zero failures/errors/skips. A new
fault check proves that changed maps invalidate device-map reuse. The production
neural arithmetic, queue layout and numerical budgets are unchanged.

This is a partial performance repair, not compliance with the full-run ceiling.
GPU evaluation and full edge-queue checking still dominate. No 1,000-step
preservation rerun or matrix launch is authorized by this timing result. The
qualification test runner now enforces its five-minute budget, kills its owned
process group on expiry and returns an explicitly unaccepted result with no
trusted counts. Routine affected checks must verify completion and timeout paths.
Continue bounded diagnosis; preserve every discrete/state check. All estimates
refer to the agent's own elapsed execution time including investigation, edits,
tool runs, tests and verification, not hypothetical human engineering effort.
The full-run time ceiling remains unresolved; do not assume a matrix exemption.
A 90%-confidence estimate for remaining bounded harness diagnosis and delivery is
**30–120 minutes of agent execution once the run-budget scope is resolved**.
The whole-goal interval below is conditional on permission for the required
scientific experiment runtimes; it remains provisional until a paired case can
be timed under an agreed budget.

Delivery: `b626b4c` and `f571f0b` passed automatic commit/push checks and are on
`origin/main`. Hosted CI `38653169030` passed for the first repair; exact-revision
CI `38653765395` passed for the map-reuse/timeout repair (59-second job, including
25 seconds for affected checks/tests). No native or pinned data test is running.
Remaining full preservation and matrix/batch runs are held:
the measured 32-step workload still predicts an over-five-minute preservation
case. Resolve whether the five-minute ceiling also covers the originally required
full-network scientific experiments before starting those runs. No exception has
been assumed and no acceptance gate has been removed.

The failed initial setup baseline and inspected end-to-end export/comparison
outputs have completed their consumers; their retention exceptions are released.
Keep the current local scientific, input, profile/native-equivalence and future
matrix bundles for the remaining qualification and performance decisions.

### Implementation baseline and unverified requirements

Source inspection at `9f89ef6` finds working code paths for the five experiments,
canonical persisted/reloaded replay, uncompiled float32 Metal simulation,
factored destination-bucket reduction, six-column Parquet output (including
typed empty output), diagnostic comparison, paired Brian2/MLX observations,
fresh repeats, CPU PyTorch comparison and first-cause capture. Batch collectors
and verifiers exist; a complete-matrix/batch orchestration command does not.
The production voltage update is still the original coupled expression; the
increment expression in the numerical contract is prospective only.

At the initial implementation checkpoint only the seven independent fixtures and
two operational quality caches survived. No full-network execution bundles survived.
Historical suite counts, removed raw
outputs and passing routine tests establish **zero currently verified cases out
of 52**. At that checkpoint source had not passed fresh local scientific, layout,
fan-in, pulse, repeatability, four-trial batch or end-to-end export checks in
this implementation phase. A case with a first spike difference is conservatively
unaccepted by the existing reporter pending a bound causal decision; metric
success alone must never be reported as case acceptance.

Further source inspection found two provenance gaps to repair before matrix
qualification: `parity_case.run` does not request/persist the existing bound
compiler context, and `persist_stimulus` does not explicitly record channel class
and event amplitude. The latter are implicit in experiment order and the fixed
model rule. Keep the six spike columns, pinned schedules and reference arithmetic;
make these required scientific records explicit. No new backend abstraction is
needed. Decision confidence: 95%, reviewed at `e519de7`.

Commit `e4f9d92` now records channel class and amplitude without
changing event bytes, persists the bound reference producer/compiler/header/input
and executable provenance, and records launch/source identity for singleton and
batch execution. New matrix and batch commands compose the existing collectors,
repeat verifiers, metric rules and source validators. The matrix independently
checks all canonical prefixes/trials, rescores native outputs, and reports group
coverage and 100 ms localization. Batch comparison uses exact equality as a
sufficient state-budget proof; differences remain unaccepted. No numerical kernel,
protected reference, pinned input or tolerance changes are included. Commit/push
hooks and all selected automatic affected tests passed. The changed
paired driver passed its focused real-framework check in 20.12 seconds; inspection
verified its reference producer digest, executable hash, actual frozen compiler
flags, 442 consumed headers and 63 generated/input files. Two earlier direct test
launches stopped during fixture setup because the explicit precision environment
and fresh temporary parent were missing; neither executed numerical checks.
Hosted exact-revision CI `38645807445` remains pending at this checkpoint.

That exact code revision's hosted CI subsequently passed. End-to-end source
inspection found one concrete empty-output defect: `parity_rates.csv` had a blank
header when both input rasters were empty. Commit `c4556ce` preserves the nine
existing column names for an empty table and extends the existing installed-CLI
file-contract check to cover that case. This changes file serialization only;
the legacy diagnostic empty-score convention and scientific gates stay intact.

Fresh scalar audits both passed: 157/157 one-step and trajectory cases in the
factored and production-layout paths, with exact count expansions, fresh-repeat
and singleton/batch component equality. Command times were 1.464 and 3.195 seconds.
Maximum factored one-step budget fraction was 0.023660. The other four required
audits subsequently passed; all six commands took 284.477 seconds in total. Each
fan-in path checked 24,576 cases across 31 targets with zero failed applicable
flags; all target archive hashes and native flags were inspected. The 99
original-state one-step conversion limitations remain explicit, never passes;
the required identical-stored-state one-step and original-state trajectory
budgets all passed. Worst required fan-in budget fractions were 0.023781/0.024415.
Complete device-row round trips, all five source/receiving patterns and both
budgets passed. The pulse proved 20 steps/two trials in original and outgoing-
silenced modes, exact complete masks/queues/unaffected states, and unchanged
arrival/influence steps 18/19. No broad preservation rerun was launched.

Pinned production CLI runs and self-comparison round trips also passed on 20 steps:
two-class/two trials exported 19 spikes; silent/one trial exported a typed empty
file. The six Parquet columns/types, schedule bytes/classes/amplitudes and hashes,
comparison JSON/CSV outputs and empty CSV headers were verified. Elapsed command
and consumer times were 11.557 and 12.345 seconds. These are workflow checks, not
independent scientific parity or repeatability acceptance.

The inspected host has Apple M1 Max, 32 GiB memory, approximately 225 GiB free
disk, Python 3.10.14, MLX/Metal 0.32.3, NumPy 1.26.4, Brian2 2.8.0 and PyTorch
2.11.0. Metal is available and the precision setting is zero. Compilation stays
disabled. Fresh local qualification outputs are retained for verification and
measured planning. The host input audit passed all 15,091,983
rows: pinned hashes, orientation/identifier ordering, stable reversible grouping,
exact count conversion and outgoing-only silencing. Maximum absolute-count sum
is 69,948 (guard: 2^40); maximum in-degree is 10,356. This is input equivalence,
not dynamic or full-network scientific acceptance.

The first implementation repair makes `qualify` prepare its required four-trial,
1,000-step frozen sugar stimulus and explicit pinned dataset environment, then
run the existing native-artifact consumer after its producers. The former runner
omitted both prerequisites and omitted that consumer. Numerical code is unchanged.
Automatic affected tests and a fresh full command must establish the repair;
source inspection alone is not a qualification pass.

The baseline finished unaccepted in 290.35 seconds: 375 collected, 351 passed,
five failures (missing explicit pinned dataset path) and 19 setup errors (missing
`FLY_BRAIN_REFERENCE_BASELINE`). Zero skips; no numerical failure was reported
among the checks that executed. The historical-reference fixture now executes
exact source bytes from immutable commit `79f62adee10b092fcaaaed0ea4043da3f5b9c415`
directly from Git, preserving the independently recorded full Torch source hash
and all native tensor comparisons. It needs no deleted external checkout or
preservation copy. This fixes test setup, not reference arithmetic.

The repaired complete run finished in 2,948.68 seconds: **375 passed, one failed,
zero errors/skips**. All five full pinned observation-preservation producers and
their complete native-byte artifact consumer passed. These six checks consumed
2,656.310 seconds (90.13% of summed test duration); the remaining 370 checks took
290.925 seconds. Launching this preservation work before implementation was an
avoidable scheduling mistake. Its outputs remain available; do not repeat it for
an unrelated fixture fix. The lone failure read a virtual Git source identity as
a filesystem path. Reading the same hash-checked immutable source directly fixes
that consumer while preserving AST, parameter order, scalar type and value checks.
The failed target alone then passed in **1.04 seconds**. The complete command's
recorded exit remains failed; this targeted repair does not rewrite that result.
No numerical failure occurred in these local checks; full-network parity is still
unverified. Scientific outputs remain subject to the registered consumer holds.

Delivery: `614ed23` (plan/retention) and `85630e1` (local runner prerequisites and
consumer) passed commit/push hooks and exact-revision hosted CI runs `38637520665`
and `38637855298`. The runner commit's first hook attempt exposed a new test's
global subprocess patch intercepting NumPy's lazy testing import; using a direct
array-equality assertion repaired that test isolation issue. Its succeeding
automatic affected invocation passed all 133 selected tests. This routine evidence
does not replace scientific qualification.

### Bounded implementation plan and completion criteria

1. Finish the demonstrated workflow/provenance gaps and minimal matrix/batch
   orchestration before another broad run. Use completed local proofs where their
   actual dependencies are unchanged; keep precise limits and source identity.
2. Repair demonstrated numerical causes using the smallest change. The approved
   voltage-increment prototype may be tested if evidence warrants it; adoption
   requires all prescribed local numerical, discrete, repeat, batch/chunk and
   observation checks. Do not change the independent references or budgets.
3. Run only outstanding local scientific requirements: prescribed 157-case scalar,
   pinned fan-in, production layout, device-row and connectome-pulse audits as
   needed after inspecting the existing run's coverage. Preserve exact schedules,
   repeats, common-history coverage and first-cause evidence. Time one shortest
   paired case as the first required matrix case, retaining it for later consumers;
   avoid a throwaway benchmark followed by an identical qualification rerun.
4. On the delivered arithmetic/mode, run all 52 prescribed paired cases twice
   per engine, check canonical prefixes and distinct trials, and report every
   absolute/paired gate without pooling away failures. Diagnose and repair
   failed gates; rerun affected scientific evidence after numerical changes.
5. Compare prescribed sugar and P9 four-trial one-second batches with independent
   trials 0–3, including exact events/discrete state, state budgets, final queues
   and repeats. Produce pooled and 100 ms localization reports separately.
6. Verify required output formats/provenance and every applicable numerical,
   discrete, repeatability, batch and causal gate. Record bounded results and
   limitations before working outputs expire. Deliver incremental hooked commits
   to `origin/main`, require successful exact-revision CI and a clean tree.

Progress: **30%** of this implementation goal, based on an explicit work breakdown:
baseline/scope inventory 10%, end-to-end workflows 10%, local scientific gates
15%, demonstrated implementation repairs 15%, 52-case qualification 30%, batches
10%, final evidence/delivery 10%. Inventory earns 10 points, workflow/provenance
and inspected end-to-end outputs earn eight, fresh local/input/reference evidence
earns eight, and demonstrated harness/serialization repairs earn four;
scientific acceptance remains 0/52. Reassess weights if measured work changes
the scope; do not derive scientific acceptance from code coverage or test counts.

Remaining-time estimate (90% confidence planning interval): **7–42 elapsed days**
on this one local host, provisionally including serial qualification and repairs.
This is engineering judgment before timing a current paired case, not a measured
performance claim. The matrix alone requires 1,231,000 steps per engine per
repetition (2,462,000 with fresh repeats), plus local and batch work. Replace this
interval with measured throughput and revised repair uncertainty after the first
paired case; revise again after each material implementation/measurement result.

Current timing evidence: ordinary full-connectome observation proof blocks
0–480 took 60.1475 seconds between writes, or 0.12531 seconds per step including
proof serialization. This is a partial producer measurement, not an ordinary
simulation benchmark or paired-observer throughput. It does not yet justify
narrowing the interval; full paired timing and repair uncertainty remain open.
The complete 1,000-step ordinary producer finished in 139.281 seconds. The four-trial
preservation producer took 1,422.598 seconds. These include proof capture and
instrumentation; neither is a paired-matrix throughput measurement. Avoiding a
repeat of unchanged preservation saves approximately 44 minutes per broad run;
it does not yet justify narrowing the remaining-time interval.

Fresh CPU reference diagnostics passed on this host. `probe-replay` regenerated,
reloaded and prefix-checked canonical fixture hash
`f1da12a8a7f3a44198fe04a385f897f991eadea36f680bf5d668ed19343fa09d`;
two NumPy runs and two independent C++ builds each produced 43 spikes, zero
state difference and exact discrete/last-spike/repeat equality. The threshold
quarter-ULP counterexample and serial cancellation limitation remain explicit.
`inspect-reference` reproduced the native phase ordering and unchanged PyTorch
conductance/voltage delay steps 20/21. No reference arithmetic was changed.
These diagnostic reports were inspected before their verification consumers
finished; their raw working outputs expire under the normal cleanup policy.
Their bounded conclusions are not full-network or MLX acceptance.

Execution holds: full-matrix acceptance and production adoption of new arithmetic
remain held until their gates pass. No hold prevents fresh baseline diagnosis or
the smallest authorized implementation repairs. No scientific acceptance claimed.

### Historical refactor scope (complete)

Finish rearchitecture/refactor and cleanup for handoff to the prior implementation
agent. The user's latest amendment rejects architecture whose complexity outweighs
the application. Concrete backend dependencies are acceptable: production remains
MLX-only. Assess each rule for this project instead of following the generic
strict profile blindly. Decision confidence: 99%, reviewed at `5249fc5`.

This amendment supersedes the former requirement to finish all 37 strict predicates
and the architecture hold tied to that analyzer. Completing runtime call-target,
alias/effect/control-flow analysis, portable numerical values and provider-neutral
model execution is outside this refactor. The experimental analyzer is retired;
its former roadmap and missing capabilities are not project completion blockers.
Do not claim the retained checks provide complete semantic analysis.

The user now requests executable project-specific checks followed by a new
practical refactor. At `3d56937` the plan is: replace broad role/fingerprint gates
with checks for actual project boundaries and protected scientific sources, then
remove a demonstrated source of application indirection. Decision confidence: 95%.
The required tests must accept concrete MLX backend contracts and framework-based
qualification models while rejecting real production/reference mixing, invalid
source identity, type failures and changed-behavior regressions.

The user's latest instruction requires single-threaded execution. All three
subagents are stopped. The parent owns all remaining code, tests, documents and
delivery; do not delegate again without a newer user instruction. Inspect current
files and commits rather than relying on historical worker context. The enforcement
worker completed clean commit `feebbea348b33f1979acdc763c8de1af01bbf496` in
`/private/tmp/fly-brain-metric-facts-20261014-01`; the other two workers left no
new changes. That commit is adopted and pushed. `d24754d` delivers the five comparison
callback removals. The parent completed the retired-platform removal directly in
`b439fdf497bcbbcbc1d575dc0a0ccd65e5ac4584`. All three commits passed automatic
local checks and are pushed. No parent test replay was added. Hosted verification
passed for all three exact code revisions; the evidence record contains run IDs.

## Historical refactor completion criteria

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

These were the refactor-only criteria. The implementation amendment above now
authorizes numerical implementation and complete scientific qualification;
unrequested performance features remain outside scope.

## Delivered cleanup and verification

The earlier tool/test cleanup is delivered through `5249fc5` on `origin/main`. Its
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

At that earlier checkpoint, the code-change hosted check passed 177 selected tests,
with 9 deselected, in 74.13 seconds; this is not a full application-suite benchmark. The final
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

The retired strict registry is replaced by a compact five-source scientific
manifest, preserving every hash and provenance field. Old capability records and
ordinary binding/classification fingerprints are removed. The
[coverage record](docs/agent/quality-coverage.md) distinguishes required checks,
review guidance and experimental mechanisms.

## Refactor completion and handoff

The practical checks are delivered at `feebbea`, the five callback getters are
removed at `d24754d`, and the retired platform and exclusive tests are removed at
`b439fdf`. The retirement removes 15,729 net lines while retaining the actual
import/type/input/metric checks and five-source scientific guard. No application,
pinned-input or independent-fixture source changes occur in that retirement.
Local automatic checks and exact hosted run `38634165371` passed: 384 affected
tests passed, 128 checker cases were deselected and two dependency warnings were
reported in 194.59 seconds. All static checks and five scientific-source checks
passed. This is a retirement/tooling selection, not a full-suite benchmark.
The code is pushed to `origin/main`; this document records the final handoff.
The bounded refactor/cleanup is complete and ready for the prior implementation
agent. Completion decision confidence: 95%, reviewed at `b439fdf` against the
criteria above. Scientific implementation and qualification remain unfinished.

The preceding rule assessment established no application defect behind the former
six findings. Any source cleanup must identify a concrete problem,
its affected callers, the smallest repair and meaningful verification before
implementation. Do not resume the generalized analyzer or tensor-contract program.
The prior implementation agent can continue under the unchanged numerical
contract, in this order:

1. Read this milestone, the numerical contract and the current source. Establish
   the implementation's actual qualification status from surviving inputs and
   fresh evidence; deleted historical outputs are not reproducible current proof.
2. Choose a bounded next scientific implementation/qualification step. Preserve
   the five protected sources, seven fixtures, exact model rules and existing
   numerical budgets. Qualify changed arithmetic or execution modes before adoption.
3. Complete the prescribed 52-case paired matrix and sugar/P9 four-trial batch
   comparisons, with fresh repeats and causal diagnosis of any failed gate.

There is no prerequisite to finish the retired analyzer plan. The former cleanup
agent stopped implementation at this handoff. The current implementation phase
is governed by the newer task and criteria above.

The complete 52-case scientific matrix and prescribed sugar/P9 four-trial
comparisons remain unfinished. Removed historical records do not establish current
source or execution-mode acceptance. Fresh qualification must satisfy all existing
scientific gates before its working outputs expire. No scientific acceptance or new
execution mode is approved by the architecture amendment.

## Checkout and ownership

Use current `origin/main`. The delivery checkout is
`/Users/ocasta/.codex/worktrees/pr-split/fly-brain`; the original
`/Users/ocasta/Code/fly-brain` remains an unchanged detached historical checkout.
The parent owns shared policy, documents, retention and serial delivery. All
workers are stopped; do not resume or delegate without a newer user instruction.
No message has been sent to the implementation chat.

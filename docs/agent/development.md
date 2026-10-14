# Developer and qualification workflow

Audience: agents and maintainers. [README.md](../../README.md) owns normal use.
Read [milestone.md](../../milestone.md) before running diagnostics; it owns
current work and evidence requirements. The [numerical contract](numerical-contract.md)
owns scientific acceptance.

## Environment and quality checks

Python dependencies use uv. Metric tooling uses Node.js 22 or later and pnpm
10.10.0, as declared in [package.json](../../package.json).
[justfile](../../justfile) defines the shared commands:

```sh
just bootstrap
just check commit
```

`just bootstrap` installs locked development/qualification dependencies, validates
pre-commit configuration, and installs commit/push hooks. `just check commit`
selects changed indexed inputs and affected dependents for formatting, lint,
strict typing, project import boundaries, protected scientific-source hashes and
advisory numerical metrics. It
runs the selected tests automatically after those checks and blocks a failing
commit. The selection includes staged and pending delivery changes since
`origin/main`, so it covers the revision CI will receive. CI uses the same
affected-test runner. Agents do not add manual pre-commit pytest calls.
`just check push` validates the submitted static source range without running
tests; `just check manual` also leaves test execution to the automatic boundaries. Current native
imports and every submitted changed path select affected dependents. Python
deletions and renames conservatively widen static type/import checks while tests
remain selected by actual surviving changes and consumers. Changed compiler/tool/configuration inputs invalidate their scope.
Import/type tools load supporting context without re-evaluating every source.
The custom compiler/native SDK and its impact platform are removed. The changed
metric bridge receives a Node syntax check; ordinary Python uses Pyright. Invalid
required inputs and actual tool failures remain blocking.
Metrics preserve complete inventory arithmetic and every commit/merge-parent
comparison. Numeric per-blob facts are reused across commands in
`logs/quality/metric-facts.json`; unchanged warm blobs are not read or recalculated.
Cold or incompatible analyzer identities require fresh calculations. The identity
binds qualified engine bytes, canonical configuration and bounded native/Python
runtime inputs; it does not prove arbitrary external dependency integrity.
Malformed facts fail analysis. No persistent test or quality verdict is cached.
Numerical metric regressions (CQ001/CQ002/CQ003) are advisory project diagnostics,
not commit blockers. The native status, values and findings remain unchanged in
reports; `project_policy` records the project decision and native exit. Invalid
results, unknown rule IDs, empty failed reports and analyzer/tool failures still
block. Package metric-check aliases use this same project gate.
Code health and maintainability index are identical custom scores; neither has a
blocking threshold. Whole-file complexity, repository averages/maxima, cognitive
heuristics and nonblank line counts are diagnostic trends. No requirement makes
every score improve on every commit. Function-level complexity review requires
a reliable function-level analyzer; the current gate does not implement one. This gate does not run the complete application
or scientific suite. Current executable coverage and limits are in
[quality-coverage.md](quality-coverage.md).
The [metric provenance](../../tools/code-quality/provenance.json) binds the
vendored standalone package to its source and both exact authored patches.
Version 0.1.1 counts whole-file native decisions; version 0.1.2 adds numeric fact
persistence and passes the same calculation map across Git comparisons. Snapshot,
calculator, inventory, aggregate and regression-predicate bytes remain unchanged.
Provenance, source/qualified archives and both patches are indexed gate inputs.

Developer diagnostics belong in ignored `logs/`; execution working data belongs
in ignored `executions/`. Successful commit and push hooks delete both folders
and legacy `.quality-reports/` outputs by default. Cleanup refuses symlinked
roots and versioned output files. Failed hooks retain diagnostics until the
failure is resolved.
Before a run or output must cross a commit, add its exact checkout-relative path,
current operational `reason`, and `release_when` condition to
`tools/code_quality/retention.json`. No blanket scientific exception applies.
Register unfinished repeat, batch, scoring or failure-review work before
committing; remove its exception when that consumer finishes. Record concise
current status in `milestone.md` and completed component checks in
[refactor evidence](refactor-evidence.md), without generated reports or
preservation copies.

Quality checks print short success summaries. Failures show bounded output and
retain a diagnostic file under `logs/quality`, capped at 64 KiB of text with
explicit omissions. Metric summaries include complete finding counts and at most
twenty examples, with no repeated file inventories. Hosted checks print bounded
diagnostics without uploading report artifacts. `just check manual` keeps its diagnostics locally.
The commit and CI gates select focused pytest targets for actual changed
behavior and affected consumers, then invoke pytest once per gate. Adopt checked
worker descendants by fast-forward to avoid a second local integration test run.
Do not add a separate manual run or repeat tests in the push hook.
Default application selection excludes reviewed `checker` exercises even where
those files live under unit/integration folders.
Do not run the whole checker suite, hook-simulation matrices or guard-weakening
exercises as routine project verification. A checker implementation change can
receive focused ordinary behavior tests; no broad self-qualification is required.
Diagnostic commands show at most twenty summary fields and ten examples per
failure category, scan every actual flag, and keep full scientific reports in
the execution bundle. The console view does not grant scientific acceptance.
Read diagnostic files in targeted chunks rather than loading entire run bundles
into the agent context.

Hosted execution uses `just check ci` when repository variable
`QUALITY_CI_TEMP_DB_CACHE_APPROVED` is true. The project authorization in
`AGENTS.md` covers the hosted pre-commit SQLite cache and its automatic runner
teardown. `milestone.md` records current verification status. Local fixtures
retain their cache at `/private/tmp/fly-brain-pre-commit-cache` outside fixture
cleanup.
This cache belongs to the development tool. The application has no database;
its storage adapters handle connectome inputs and simulation result files.

Brian2 and PyTorch are qualification references; their central processing unit
(CPU) execution is separate from the MLX production runtime. Apple's command
line compiler tools are required for C++ reference builds. Bootstrap sets
`MLX_ENABLE_TF32=0` before loading MLX and rejects an explicit unsafe setting.
Production uses float32 Metal arrays and explicit streams; CPU propagation
fallback is unsupported.

## Application and scientific checks

Run from the repository root. Every output path must be new.

```sh
uv run --locked --group qualification python -m pytest \
  --ignore=tests/integration/test_session_proof_artifacts.py
uv run --locked --group qualification fly-brain qualify --output executions/qualification-01
```

Default pytest selection covers application unit and file/process integration
tests. Ordinary development relies on automatic affected tests; the full command above
is for an explicitly requested full application run. The proof-artifact integration consumer needs a fresh full native
proof bundle; refactor verification reports its exclusion explicitly. When
choosing a repository-local pytest temporary root, use a fresh path under
`executions/`: application fixtures create scientific working data and must not
run under `logs/`. Timing summaries and JUnit diagnostics belong under `logs/`.
Per-test timings (`--durations=20`) can identify quality-harness overhead without
running a new full scientific matrix. Completed timing measurements belong in
[refactor evidence](refactor-evidence.md);
[milestone.md](../../milestone.md) owns the current work and acceptance status.
`qualify` exercises the independent reference and MLX scientific suites on a
real Metal device. It prepares a fresh canonical four-trial, 1,000-step sugar
stimulus, sets the pinned dataset root explicitly, and runs the native-artifact
integration consumer after the scientific producers. Historical reference
preservation tests load the exact pinned Git revision in memory and check the
independent original Torch source hash; they require complete Git history, not
an external baseline checkout. Its logs, reports and state/event arrays are working inputs
to verification. They expire at the next successful commit unless an explicit
remaining consumer is registered. Skipped, missing, empty, or failed required
results prevent acceptance.

During implementation, fix and rerun only the failed scientific targets instead
of restarting `qualify`. Keep completed expensive proofs while their verification
consumers need them, and repeat them when affected source/input changes require
it. Finish workflow and provenance changes before full qualification. The current
milestone requires less than 10% of working time in idle test waiting; account for
scientific and automatic-check waits too. Do useful independent work during long
runs, and report any measured conflict with mandatory acceptance instead of
silently omitting gates or counting idle execution as implementation work.

One prescribed full-connectome parity case:

```sh
uv run --locked --group qualification fly-brain qualify-parity \
  --experiment p9 --duration-s 0.1 --trial 0 \
  --output executions/parity-p9-0.1-0-01
```

It runs all three engines twice from fresh state with a persisted canonical
schedule. Channel metadata explicitly records class, rate and amplitude, including
duplicate and zero-rate channels. `launch.json` and `environment.json` record the
launch commit, complete package source inventory and execution settings.
`reference-job.json` binds the actual compiler, consumed headers/dependencies,
generated model, input arrays and executable. `case.json` retains frozen metrics and native state/queue/cause
verification. First differences require scientific review. One accepted case
cannot establish complete-matrix acceptance.

After implementation and outstanding local scientific requirements are ready,
run the complete prescribed matrix and both batch comparisons:

```sh
uv run --locked --group qualification python -m tools.qualify_matrix \
  --output executions/matrix-01
```

The controller must match its committed source before launch. It verifies all 52
canonical inputs against independent PCG64 generation, regeneration, reload,
duration prefixes, singleton/batch identity and outgoing-silenced replay. Every
case runs fresh repeats, is rescored from native spikes, and has its source hashes
checked against its launch and the current checkout. It stops at the first
unaccepted or invalid case and writes incomplete coverage as unaccepted.
`matrix.json` keeps per-case gates, pooled metrics and per-trial/pooled 100 ms
counts. All case outputs remain available for repeat, batch and causal consumers.
Do not modify numerical/observer sources while their qualification is running.

The same batch workflow can consume completed one-second singleton cases:

```sh
uv run --locked --group qualification python -m tools.qualify_batch \
  --experiment sugar --singletons executions/matrix-01/cases \
  --output executions/sugar-batch-01
```

Use `--experiment p9` for the other prescribed batch. It requires accepted
singletons 0–3, byte-identical canonical schedules and compatible recorded execution
settings/sources. Fresh four-trial MLX and CPU reference runs are repeated, then
compared with the independent trials. Exact native phase/final equality is a
sufficient state-budget proof; a difference remains unaccepted pending diagnosis.
These commands do not grant acceptance when local or causal gates are unresolved.

## Diagnostic command inventory

Use the shared command form with a fresh output directory:

```sh
uv run --locked --group qualification fly-brain <command> --output executions/<fresh-directory>
```

| Command | Recorded scope |
| --- | --- |
| `probe-accumulation` | Serial precision/cancellation limitation; successful diagnostic assertions do not imply parity |
| `probe-factored` | Compensated common-scale scalar arithmetic |
| `probe-bucketed` | All 157 retained scalar cases through destination layout and event gather |
| `probe-replay` | Retained deterministic reference state/event replay |
| `inspect-reference` | Original reference schedule and delay observations |
| `audit-inputs` | Host pins, identifier order/direction, signed counts, row identities, guards, and reversible grouping; no simulation |
| `qualify-fan-in` | Complete prescribed pinned target/mask/state/order arithmetic audit |
| `qualify-layout-fan-in` | The same audit through actual source identity and production destination layout |
| `qualify-device-layout` | Every original-row field/event and padding leaf across five source/receiving patterns |
| `qualify-connectome-pulse` | Complete-network 20-step, two-trial pulse, queue/gate/unaffected-state checks, and outgoing-silenced repeat |

Fan-in qualification keeps both original-weight references, exact event
membership, repeat/standalone comparisons, original-state conversion limits,
and required trajectory budgets. Controlled construction/delivery checks do
not replace full-network experiment parity.

## Code ownership

| Path | Owns |
| --- | --- |
| `src/fly_brain/simulation` | Network/stimulus values, MLX core, accumulation, propagation, input/output and owned command adapters |
| `src/fly_brain/qualification` | Requests, acceptance, orchestration, independent references, diagnostics, process/file and owned command adapters |
| `src/fly_brain/comparison` | Spike values, pure comparison rules, request validation, Parquet/report and owned command adapters |
| `src/fly_brain/bootstrap.py` | Dependency composition and process configuration |
| `src/fly_brain/cli.py` | Argument parsing, validated request/command selection, one composed owned command call, and exit propagation |
| `tests` | Unit, integration, scientific qualification, source-only quality checks, and injected support |

Owned command adapters print results and map command exit status. Detailed
classifications and representation limits belong to
[Source ownership](architecture-ownership.md).

Import-linter enforces the configured domain/framework boundaries. Pyright
checks owned code in strict mode. [Typing limits](typing.md) own the rationale
for local third-party stubs and narrow suppressions.

The seven independent regression fixtures live under `tests/data/reference`.
Their exact paths, current consumers, and release conditions are registered in
[the retention manifest](../../tools/code_quality/retention.json). Current
qualification uses fresh outputs and every required scientific gate.

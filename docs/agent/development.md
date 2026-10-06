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
just check
```

`just bootstrap` installs locked development/qualification dependencies, validates
pre-commit configuration, and installs commit/push hooks. `just check` runs
formatting, lint, strict typing, import boundaries, source-only quality tests,
and staged/commit metric regression checks. It does not run the complete
application or scientific suite. Current executable coverage and limits are in
[quality-coverage.md](quality-coverage.md).
The [metric provenance](../../tools/code-quality/provenance.json) binds the
vendored standalone package to its original source plus the exact qualified
Python aggregation patch. Version 0.1.1 counts whole-file native decisions;
older metric numbers retain their original 0.1.0 identity. Both archives remain
versioned, and provenance/archives/patch are canonical indexed gate inputs.

Hosted execution uses the same command when repository variable
`QUALITY_CI_TEMP_DB_CACHE_APPROVED` is true. The project authorization in
`AGENTS.md` covers the hosted pre-commit SQLite cache and its automatic runner
teardown. `milestone.md` records current verification status. Local fixtures
retain their cache at `/private/tmp/fly-brain-pre-commit-cache` outside fixture
cleanup.

Brian2 and PyTorch are qualification references; their central processing unit
(CPU) execution is separate from the MLX production runtime. Apple's command
line compiler tools are required for C++ reference builds. Bootstrap sets
`MLX_ENABLE_TF32=0` before loading MLX and rejects an explicit unsafe setting.
Production uses float32 Metal arrays and explicit streams; CPU propagation
fallback is unsupported.

## Application and scientific checks

Run from the repository root. Every output path must be new.

```sh
uv run --locked --group qualification pytest
uv run --locked --group qualification fly-brain qualify --output data/results/qualification-01
```

Default pytest selection covers unit, file/process integration and source-only
quality tests.
`qualify` exercises the independent reference and MLX scientific suites on a
real Metal device and retains logs, reports, measurements, and state/event
arrays. Skipped, missing, empty, or failed required results prevent acceptance.

One prescribed full-connectome parity case:

```sh
uv run --locked --group qualification fly-brain qualify-parity \
  --experiment p9 --duration-s 0.1 --trial 0 \
  --output data/results/parity-p9-0.1-0-01
```

It runs all three engines twice from fresh state with a persisted canonical
schedule. `case.json` retains frozen metrics and native state/queue/cause
verification. First differences require scientific review. One accepted case
cannot establish complete-matrix acceptance.

## Diagnostic command inventory

Use the shared command form with a fresh output directory:

```sh
uv run --locked --group qualification fly-brain <command> --output data/results/<fresh-directory>
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

## Historical recovery

[Architecture remediation](history/architecture-remediation.md#retired-source)
records retired workflows and exact Git recovery commands. Historical result
bundles retain their original environment scope. [Reference history](history/reference-baseline.md)
owns original source measurements and notices. [Evidence](../evidence/) stays at
its original paths with recorded source/environment bindings.

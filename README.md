# Fly-brain on Apple MLX

This application targets Apple silicon and uses MLX for simulation. It is based on the FlyWire v783 leaky integrate-and-fire model from [Eon Systems](https://github.com/eonsystemspbc/fly-brain), pinned at `a3db62f9436074e485c0278290c2164ed6150808`.

The numerical core, complete connectome mapping, device propagation, and controlled delivery are qualified. The normal installation runs the complete shortest sugar experiment twice with byte-identical outputs; the complete silent control produces zero spikes. Existing comparison tools consume populated and empty exports. Full-network scientific parity and performance remain open. See [the authoritative plan](milestone.md), [the numerical contract](docs/agent/numerical-contract.md), and [project rules](AGENTS.md).

## Install

Use macOS on Apple silicon, Python 3.10.14, and uv. One project and lockfile define the environment. Conda and NVIDIA execution backends have been removed.

```sh
uv venv --python 3.10.14
uv sync --locked --no-dev
uv run --locked --no-dev fly-brain --help
```

The application dependencies are MLX, MLX Metal, NumPy, Pydantic, and PyArrow. Pydantic validates external requests. PyArrow reads the existing Parquet spike files. No database or database framework is used.

For development and scientific qualification, add the qualification dependency group:

```sh
uv sync --locked --group qualification
```

Brian2 2.8.0 and PyTorch 2.11.0 are independent CPU references required by the frozen numerical contract. They are absent from the default runtime installation and are not application execution backends. The same uv project manages both groups.

The C++ reference replay also requires Apple's command line compiler tools.

## Run

Run a complete sugar experiment from this checkout:

```sh
uv run --locked --no-dev fly-brain simulate --duration-s 0.1 --trials 1
```

The default creates a new directory under `data/results`. Use `--output` for a specific new directory and `--project` when running outside the checkout. `--experiment` selects `sugar`, `p9`, `sugar-silenced`, `two-class`, or `silent`. The original neuron identifiers, channel rates, and outgoing silencing are preserved.

Each run writes the canonical stimulus before execution and reloads its exact event bytes. It records schedule/data hashes, per-trial seed provenance, source/dependency versions, timing stages, and MLX allocator peak. Spike files use the existing six-column Brotli Parquet contract, including typed empty outputs. Neural state remains on Metal; collection transfers bounded blocks of spike events.

## Verify

Run from this checkout. Use a new output directory each time; commands reject existing output directories.

```sh
uv run --locked --group qualification ruff check .
uv run --locked --group qualification ruff format --check .
uv run --locked --group qualification pyright
uv run --locked --group qualification lint-imports --no-cache
uv run --locked --group qualification pytest
uv run --locked --group qualification fly-brain qualify --output data/results/qualification-01
```

The default pytest selection covers unit tests and file/process integration tests. The `qualify` command runs the independent reference, serial MLX core, and factored qualification cases on a real Metal device. It records logs, the test report, measurements, and complete state/event arrays. A skipped test, missing report, empty suite, or failed test prevents acceptance.

Run one prescribed full-connectome parity case:

```sh
uv run --locked --group qualification fly-brain qualify-parity \
  --experiment p9 --duration-s 0.1 --trial 0 \
  --output data/results/parity-p9-0.1-0-01
```

This command runs all three engines twice from fresh state with one persisted canonical schedule. It retains native state/queue replay evidence, first-cause context, validated spike coordinates, and exact frozen metric results in `case.json`. First differences require scientific review and prevent automatic acceptance. Only the 52 prescribed configurations are allowed; one accepted case does not establish full-matrix parity.

Bootstrap sets `MLX_ENABLE_TF32=0` before loading MLX. An explicit unsafe setting is rejected. The core uses float32 arrays and explicit Metal streams; CPU fallback is unsupported. Complete destination layout and controlled full-connectome delivery are qualified; full experiment parity and performance acceptance remain separate gates.

Existing scientific diagnostics are available through the installed command:

```sh
uv run --locked --group qualification fly-brain probe-accumulation --output data/results/accumulation-01
uv run --locked --group qualification fly-brain probe-factored --output data/results/factored-01
uv run --locked --group qualification fly-brain probe-bucketed --output data/results/bucketed-scalars-01
uv run --locked --group qualification fly-brain probe-replay --output data/results/replay-01
uv run --locked --group qualification fly-brain inspect-reference --output data/results/schedule-01
```

The serial accumulation diagnostic records an asserted precision limitation. Its successful execution does not mean every diagnostic case meets parity. Acceptance limits remain fixed in the numerical contract.

`probe-bucketed` executes all 157 retained scalar cases through the actual destination layout and event gather. It verifies both original-state budgets, exact integer count expansions, negative-zero copies, repeated results, and individual versus batched execution.

Milestone 2's host input audit verifies both pinned files, identifier order and direction, signed counts, all row identities, arithmetic guards, and stable reversible destination grouping. It retains full converted arrays and checksums in a fresh output directory:

```sh
uv run --locked --no-dev fly-brain audit-inputs --output data/results/input-audit-01
```

This command performs host setup and evidence collection. It does not simulate the full connectome.

The complete prescribed input fan-in audit is available through the installed command:

```sh
uv run --locked --no-dev fly-brain qualify-fan-in --output data/results/fan-in-01
uv run --locked --no-dev fly-brain qualify-layout-fan-in --output data/results/layout-fan-in-01
uv run --locked --no-dev fly-brain qualify-device-layout --output data/results/device-layout-01
uv run --locked --no-dev fly-brain qualify-connectome-pulse --output data/results/connectome-pulse-01
```

It preserves every target, mask, initial state, edge order, reference, and device result, with repeated and individual-run comparisons. The isolated arithmetic check starts both engines from the same stored state; original-state conversion limitations remain visible, and the original-state trajectory limits remain mandatory. A failed required case returns a failure status. This audit does not establish full-network parity.

`qualify-layout-fan-in` uses the same case builder, limits, and evidence writer. It feeds each prescribed edge order and event mask through the production layout, including actual source identifiers, target index recovery, empty targets, and untouched source states.

`qualify-device-layout` verifies every field and gathered event against all original connection rows, including every padding leaf. Five fixed source/receiving patterns cover all events, no events with negative-zero state, and seeded patterns. It retains full neuron results and both original-weight references, with exact counts and repeated/individual-run checks.

`qualify-connectome-pulse` executes 20 steps on the complete network, with two trials and an independently computed float64 pulse reference. It checks every due/accepted/discarded event, every queue slot, clocks, and exact unaffected-neuron bits. The outgoing-silenced repeat retains all event identities. This qualifies complete construction and controlled delivery; full experiment parity remains open.

## Compare existing spikes

The comparison adapter reads `trial`, `neuron_index`, and `flywire_id`, with `time_ms`, `time_s`, or the existing `t` convention. It preserves the existing matching and rounded diagnostic metrics. These metrics do not replace the future full-network acceptance gate.

```sh
uv run --locked --no-dev fly-brain compare \
  --first /path/to/mlx.parquet --second /path/to/reference.parquet \
  --duration-s 0.1 --trials 1 --tolerance-ms 0.1 \
  --output data/results/comparison-01
```

Outputs retain `pairwise_summary.json`, `pairwise_summary.csv`, and `parity_rates.csv`. Reading and comparison do not modify spike files.

## Code ownership

- `src/fly_brain/simulation`: immutable network cases and the MLX core, accumulation arithmetic, and explicit propagation factories.
- `src/fly_brain/qualification`: requests, acceptance results, orchestration, independent CPU references, diagnostics, and process/file adapters.
- `src/fly_brain/comparison`: spike types, pure comparison rules, request validation, and Parquet/report adapters.
- `src/fly_brain/bootstrap.py`: dependency composition and process configuration.
- `src/fly_brain/cli.py`: argument parsing, one application call, and result presentation.
- `tests`: unit, file/process integration, scientific qualification, and explicitly injected test support.

Import-linter enforces domain and framework boundaries. Pyright checks every application module and test in strict mode. [Narrow third-party typing limits](docs/agent/typing.md) are documented. No application path injection, database scaffolding, global run paths, or runner-to-orchestrator imports remain.

## Preserved source, data, and evidence

The original application is retained in Git history. The [architecture record](docs/agent/history/architecture-remediation.md#retired-source) lists retired workflows and recovery commands. Scientific evidence and local data remain preserved, including the incoming manual review archive.

The historical `data/results/nature_2026_07/` bundle records earlier multi-framework results. Its metadata and checksums remain available; those recorded frameworks are not supported by this application. The original spike bundle is stored in [Google Drive](https://drive.google.com/drive/folders/1jiSfb5lNfm9gwP0YyyRz5ATIrDpBAcjs). After placing it in that historical folder, verify the supplied checksums with `shasum -a 256 -c checksums.sha256` from that folder.

Source attribution and scientific references remain in the [baseline](docs/agent/numerical-contract.md) and Git history. The upstream and vendored license files are retained.

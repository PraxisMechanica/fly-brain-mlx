# Fly-brain on Apple MLX

This application targets Apple silicon and uses MLX for simulation. It is based on the FlyWire v783 leaky integrate-and-fire model from [Eon Systems](https://github.com/eonsystemspbc/fly-brain), pinned at `a3db62f9436074e485c0278290c2164ed6150808`.

The small numerical core is qualified. Full-connectome loading, a complete simulation command, production spike export, and performance qualification remain later milestones. See [the authoritative plan](milestone.md), [the numerical contract](docs/mlx-port-baseline.md), and [project rules](AGENTS.md).

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

Bootstrap sets `MLX_ENABLE_TF32=0` before loading MLX. An explicit unsafe setting is rejected. The core uses float32 arrays and explicit Metal streams; CPU fallback is unsupported. The factored adapter remains a small-network qualification candidate, with no full-connectome or performance approval.

Existing scientific diagnostics are available through the installed command:

```sh
uv run --locked --group qualification fly-brain probe-accumulation --output data/results/accumulation-01
uv run --locked --group qualification fly-brain probe-factored --output data/results/factored-01
uv run --locked --group qualification fly-brain probe-replay --output data/results/replay-01
uv run --locked --group qualification fly-brain inspect-reference --output data/results/schedule-01
```

The serial accumulation diagnostic records an asserted precision limitation. Its successful execution does not mean every diagnostic case meets parity. Acceptance limits remain fixed in the numerical contract.

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

Import-linter enforces domain and framework boundaries. Pyright checks every application module and test in strict mode. [Narrow third-party typing limits](typings/README.md) are documented. No application path injection, database scaffolding, global run paths, or runner-to-orchestrator imports remain.

## Preserved source, data, and evidence

The original application is retained in Git history. The [architecture record](docs/architecture-remediation.md#retired-source) lists retired workflows and recovery commands. Scientific evidence and local data remain preserved, including the incoming manual review archive.

The historical `data/results/nature_2026_07/` bundle records earlier multi-framework results. Its metadata and checksums remain available; those recorded frameworks are not supported by this application. The original spike bundle is stored in [Google Drive](https://drive.google.com/drive/folders/1jiSfb5lNfm9gwP0YyyRz5ATIrDpBAcjs). After placing it in that historical folder, verify the supplied checksums with `shasum -a 256 -c checksums.sha256` from that folder.

Source attribution and scientific references remain in the [baseline](docs/mlx-port-baseline.md) and Git history. The upstream and vendored license files are retained.

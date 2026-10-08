# Fly-brain on Apple MLX

Run the FlyWire v783 leaky integrate-and-fire model on Apple silicon with MLX.
This project is based on [Eon Systems' simulation](https://github.com/eonsystemspbc/fly-brain),
pinned at `a3db62f9436074e485c0278290c2164ed6150808`.

The complete shortest sugar experiment and silent control have been verified.
Full-network scientific parity and performance qualification are still in
progress. See [project status](milestone.md) for the recorded scope and limits.

## Install

Use macOS on Apple silicon, Python 3.10.14, and uv.

```sh
uv venv --python 3.10.14
uv sync --locked --no-dev
uv run --locked --no-dev fly-brain --help
```

The default installation uses MLX, MLX Metal, NumPy, Pydantic, and PyArrow.

## Input data

Run from a checkout containing the two pinned input files:

- `data/2025_Completeness_783.csv`
- `data/2025_Connectivity_783.parquet`

The loader verifies their recorded hashes and neuron ordering. Changed input
files are rejected.

## Run a simulation

```sh
uv run --locked --no-dev fly-brain simulate --duration-s 0.1 --trials 1
```

The default experiment is `sugar`. `--experiment` also accepts `p9`,
`sugar-silenced`, `two-class`, and `silent`. Use `--seed` to set the stimulus seed,
`--output` to select a new output directory, and `--project` to select this
checkout when you run the command from another directory.

Each run creates a fresh directory under ignored `executions` by default. It writes
Parquet spike events, the exact stimulus and its provenance, and a
`simulation.json` report with counts, timings, versions, and hashes. Spike files
retain the existing six-column format, including typed empty output.

## Compare spike files

```sh
uv run --locked --no-dev fly-brain compare \
  --first /path/to/mlx.parquet --second /path/to/reference.parquet \
  --duration-s 0.1 --trials 1 --tolerance-ms 0.1 \
  --output executions/comparison-01
```

Use a new output directory. Comparison writes `pairwise_summary.json`,
`pairwise_summary.csv`, and `parity_rates.csv`; it leaves the input files intact.
These diagnostic scores do not establish full scientific acceptance.

## Development and records

[Developer and qualification commands](docs/agent/development.md) describe the
quality checks and scientific diagnostics. [Agent documentation](docs/agent/README.md)
indexes the active plan, scientific contract, review records, and evidence.

The historical spike bundle is available in
[Google Drive](https://drive.google.com/drive/folders/1jiSfb5lNfm9gwP0YyyRz5ATIrDpBAcjs).
Its original metadata remains under `data/results/nature_2026_07/`. From that
folder, verify supplied checksums with `shasum -a 256 -c checksums.sha256`.

See [LICENSE](LICENSE) and the retained
[paper-model license](code/paper-phil-drosophila/LICENSE) for source notices.

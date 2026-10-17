# Experimental Apple MLX integration

This opt-in backend targets native Apple silicon macOS with Python 3.10.14.
The existing default backend selection is unchanged. The adapter uses the
standard `run_all_benchmarks` interface, benchmark CSV, labeled round manifest
and six-column Parquet schema. `t` is seconds, `time_ms` is milliseconds, and
trial, neuron-row and FlyWire identifiers remain int64, including empty outputs.
Both existing comparison tools register `mlx` and read the same exported files.
Their pandas dependency is optional for simulation; install `pandas==2.3.3`
to use them in the isolated MLX environment (test requirements include it).

## Numerical preservation

`code/fly_brain/` contains the production dependency closure copied verbatim
from PraxisMechanica/fly-brain-mlx at `abbf6a2`, whose numerical candidate is
`72627c7`. `code/mlx-runtime.json` records every original path and SHA-256.
The dispatcher and file adapter contain no replacement kernel. Compilation is
disabled and `MLX_ENABLE_TF32=0` is enforced before importing MLX. Exact pinned
MLX/Metal 0.32.3, NumPy 1.26.4 and PyArrow 25.0.1 versions are required.

FlyWire v783 data hashes, ordering and signed counts are verified. Eon's sugar
and P9 definitions match the pinned configurations. The Python API also accepts
the pinned sugar-silenced, two-class and silent configurations; unsupported
target/rate/class/silencing overrides fail explicitly. Independent channels,
outgoing silencing, delay/refractory phases and float32 operation order are
unchanged. No Brian2, PyTorch, CUDA or qualification package is imported by MLX.

`n_run` executes sequential fresh singletons. It does not select a vectorized
batch mode. Canonical PCG64 inputs use seed tuples `[20261004, generator_code,
trial_index]`; parameter-grid prefixes and repeated rounds intentionally reuse
those inputs. Repeated rounds are not independent statistical samples.

## Saved-input replay

The API accepts a retained directory containing `stimulus.json` and
`stimulus.npz`, verifies archive and event hashes, data/experiment identity,
channel classes, rates, binary dtype, seed tuples and trial identifiers, then
selects a requested horizon/trial prefix. Saved seed/identifiers are authoritative.

```python
from pathlib import Path
from benchmark import BenchmarkLogger, get_experiment
from run_mlx import run_single_benchmark

result = run_single_benchmark(
    1.0, 1, get_experiment('sugar'), BenchmarkLogger(),
    run_label='fresh_saved_input',
    stimulus_path=Path('tests/data/mlx-replay/sugar'),
)
```

Run this from `code/`, or include `code/` in Python's module path. Existing MLX
Parquet/sidecar paths are rejected; choose a fresh label. Timing-only
`--disable-spike-io` is rejected before loading an engine. Other backends retain
their existing behavior.

## Evidence and limitations

The original candidate passed 323 local qualification tests, five one-second
full-network observed cases with state/queue, paired metrics and fresh repeats,
and a 363-job independent-seed gross-error screen. Exact/oracle and historical
ten-second precision evidence retain their original hardware/scope. The 363 jobs
contained 30 trials per active experiment/cohort and three exact silent controls.
No prospective primary statistic reached 4; the maximum was 2.240, with zero
per-neuron outliers. Nine of twelve pointwise 95% count-ratio intervals fit ±2%.
P9 equivalence remains unestablished: MLX-A/Brian2 ratio 0.9028, interval
[0.8245, 0.9910]; MLX-B/Brian2 ratio 0.9498, interval [0.8571, 1.0529].
MLX-B/MLX-A is 1.0521, interval [0.9604, 1.1500]. The portable
[campaign statistics](validation/m5-statistics.json) retain the original metrics
and receipt bindings; raw campaign arrays remain in the validation checkout.
Passing screens is not equivalence or a guarantee for other inputs/horizons.

Measured M5 singleton whole-loop medians were 50–56 seconds per biological
second for MLX, versus 1.7–2.6 for Brian2. No speedup is claimed. Sampled tree RSS
peaked at 3.14 GiB for MLX and 3.69 GiB for Brian2; MLX allocator peak was
1.35 GiB. These scopes are distinct and non-additive. This integration makes no
new full-network M5 batch or ten-second acceptance claim.

Simulation time uses the existing whole-loop stopwatch, including first-step
evaluation and block collection; final sorting and Parquet writing are outside.
Setup and explicit build are separate (explicit MLX build is zero). Total time
ends after Parquet writing, before JSON sidecar/logging. Adjacent `.mlx.json`
files retain per-trial timing, memory, runtime/data/input/output hashes and seeds.

## Focused package checks

```sh
uv pip install -r requirements-mlx-test.txt
python -m pytest -m 'not metal'
python -m pytest -m metal
```

Host CI verifies optional imports, unchanged/default dispatch, CLI rejection,
runtime/fixture hashes, saved-input validation, typed exports, both comparison
loaders, and CSV/manifest compatibility. Real-Metal checks compare packaged
one-second sugar/P9 output against portable independent Brian2 native fixtures,
verify fresh sequential trials, and execute the real 0.1-second CLI in an
isolated package copy. Fixture provenance binds the original accepted trials.
These focused checks test packaging; they do not repeat the statistical campaign.

Local Apple M5 Max integration checks passed all 38 tests without failures,
errors or skips: 34 host contracts and four real-Metal checks. The two one-second
replays matched every Brian2 spike step, neuron row, FlyWire mapping and per-neuron
count exactly: sugar 16,752 spikes, P9 858. The isolated real CLI produced 1,612
matching sugar spikes over 0.1 seconds. Metal checks took 120 seconds combined.
The comparison loader now preserves numeric empty outputs and int64 trial IDs.
See [execution bindings and receipts](validation/integration-results.json).

Fixtures include original Brian2 trial receipts and observed-case reports;
hashes in `provenance.json` bind those records to the saved inputs and expected
spikes. They are self-contained for regression replay. Historical records refer
to larger retained artifacts and do not imply those raw arrays are included here.

## Attribution

The copied runtime and adapter are GPL-2.0-or-later under the root license.
Original Shiu/Spiller MIT notices and existing third-party notices remain intact.
Kisame's MIT implementation informed the earlier audit; no code was copied.
MLX/Metal retain Apple's wheel notices; metal-cpp headers are not vendored.

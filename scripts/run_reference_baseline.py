import argparse
import importlib.metadata
import json
import platform
from pathlib import Path
import sys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--experiment', choices=('sugar', 'p9'), default='sugar')
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)

    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root / 'code'))
    import benchmark
    import brian2
    import pyarrow.parquet as pq

    benchmark.path_res = output / 'spikes'
    benchmark.csv_path = output / 'benchmarks.csv'
    benchmark.output_dir = output / 'standalone'
    brian2.prefs.devices.cpp_standalone.extra_make_args_unix = ['-j2']

    logger = benchmark.BenchmarkLogger(log_file=output / 'baseline.log')
    try:
        results = benchmark.run_benchmarks(
            backends=['cpu'],
            t_run_values=[0.1],
            n_run_values=[1],
            experiment=benchmark.get_experiment(args.experiment),
            logger=logger,
            run_label='reference',
        )
    finally:
        logger.close()

    result = results['cpu'][0]
    record = {
        'upstream': json.loads((root / 'docs/upstream-pin.json').read_text()),
        'python': platform.python_version(),
        'machine': platform.machine(),
        'versions': {
            name: importlib.metadata.version(name)
            for name in ('brian2', 'numpy', 'torch', 'pandas', 'pyarrow')
        },
        'timestep_ms': float(brian2.defaultclock.dt / brian2.ms),
        'seed': None,
        'operational_overrides': {
            'result_directory': str(benchmark.path_res),
            'benchmark_csv': str(benchmark.csv_path),
            'standalone_directory': str(benchmark.output_dir),
            'make_parallel_jobs': 2,
        },
        'result': result,
    }
    if result['status'] == 'success':
        record['parquet_schema'] = str(pq.read_schema(result['spike_path']))
        record['parquet_rows'] = pq.read_metadata(result['spike_path']).num_rows
    with (output / 'result.json').open('x') as destination:
        json.dump(record, destination, indent=2)
        destination.write('\n')
    if result['status'] != 'success':
        raise SystemExit(f"Reference experiment failed: {result['status']}")
    print(f"Verified {record['parquet_rows']} output spikes")


if __name__ == '__main__':
    main()

import csv
import json
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq

from .models import ComparisonResult, Spikes


def read_spikes(path: Path, duration_s: float) -> Spikes:
    columns = set(pq.read_schema(path).names)
    time_column = next(
        (name for name in ('time_ms', 'time_s', 't') if name in columns), None
    )
    if time_column is None or not {'trial', 'flywire_id', 'neuron_index'} <= columns:
        raise ValueError(
            'Spike columns must include trial, flywire_id, neuron_index, and time'
        )
    table = pq.read_table(
        path, columns=['trial', 'flywire_id', 'neuron_index', time_column]
    )
    if any(table[name].null_count for name in table.column_names):
        raise ValueError('Spike columns must not contain null values')
    times = np.asarray(table[time_column].to_numpy(), dtype=np.float64)
    if (
        time_column == 'time_ms'
        or time_column == 't'
        and times.size
        and np.nanmax(times) > duration_s * 2
    ):
        times = times / 1000.0
    if not np.all(np.isfinite(times)):
        raise ValueError('Spike times must be finite')
    return Spikes(
        np.asarray(table['trial'].to_numpy(), dtype=np.int16),
        np.asarray(table['flywire_id'].to_numpy(), dtype=np.int64),
        times,
    )


def write_comparison(output: Path, result: ComparisonResult) -> None:
    output.mkdir(parents=True, exist_ok=False)
    with (output / 'pairwise_summary.json').open('x') as destination:
        json.dump([result.summary], destination, indent=2)
        destination.write('\n')
    for filename, rows in (
        ('pairwise_summary.csv', (result.summary,)),
        ('parity_rates.csv', result.rates),
    ):
        with (output / filename).open('x', newline='') as destination:
            writer = csv.DictWriter(
                destination, fieldnames=list(rows[0]) if rows else []
            )
            writer.writeheader()
            writer.writerows(rows)

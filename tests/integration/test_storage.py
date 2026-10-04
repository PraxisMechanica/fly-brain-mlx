import csv
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from fly_brain.comparison.models import ComparisonResult
from fly_brain.comparison.storage import read_spikes, write_comparison

pytestmark = pytest.mark.integration


@pytest.mark.parametrize(
    'column,values', [('time_ms', [1.0]), ('time_s', [0.001]), ('t', [1.0])]
)
def test_reader_preserves_existing_time_column_contracts(
    tmp_path: Path, column: str, values: list[float]
) -> None:
    path = tmp_path / 'spikes.parquet'
    table = pa.table(
        {
            'trial': np.array([0], dtype=np.int16),
            'flywire_id': np.array([720575940000000001], dtype=np.int64),
            'neuron_index': [0],
            column: values,
        }
    )
    pq.write_table(table, path)
    spikes = read_spikes(path, 0.1)
    np.testing.assert_array_equal(spikes.time_s, [0.001])
    np.testing.assert_array_equal(spikes.neuron_ids, [720575940000000001])


def test_reader_preserves_canonical_empty_parquet(tmp_path: Path) -> None:
    path = tmp_path / 'empty.parquet'
    table = pa.table(
        {
            'trial': np.array([], dtype=np.int16),
            'flywire_id': np.array([], dtype=np.int64),
            'neuron_index': np.array([], dtype=np.int64),
            'time_ms': np.array([], dtype=np.float64),
        }
    )
    pq.write_table(table, path)
    assert read_spikes(path, 0.1).time_s.size == 0


def test_reader_rejects_missing_contract_columns(tmp_path: Path) -> None:
    path = tmp_path / 'invalid.parquet'
    pq.write_table(pa.table({'time_ms': [1.0]}), path)
    with pytest.raises(ValueError, match='Spike columns'):
        read_spikes(path, 0.1)


def test_reader_rejects_nonfinite_times(tmp_path: Path) -> None:
    path = tmp_path / 'invalid.parquet'
    pq.write_table(
        pa.table(
            {'trial': [0], 'flywire_id': [1], 'neuron_index': [0], 'time_ms': [np.nan]}
        ),
        path,
    )
    with pytest.raises(ValueError, match='finite'):
        read_spikes(path, 0.1)


def test_reader_rejects_null_identifiers(tmp_path: Path) -> None:
    path = tmp_path / 'null.parquet'
    pq.write_table(
        pa.table(
            {'trial': [0], 'flywire_id': [None], 'neuron_index': [0], 'time_ms': [0.1]}
        ),
        path,
    )
    with pytest.raises(ValueError, match='null'):
        read_spikes(path, 0.1)


def test_installed_comparison_command_reads_and_writes_the_file_contract(
    tmp_path: Path,
) -> None:
    first, second = tmp_path / 'first.parquet', tmp_path / 'second.parquet'
    for path, times in ((first, [1.0, 3.0]), (second, [1.0])):
        pq.write_table(
            pa.table(
                {
                    'trial': [0] * len(times),
                    'neuron_index': [0] * len(times),
                    'flywire_id': [10] * len(times),
                    'time_ms': times,
                }
            ),
            path,
        )
    output = tmp_path / 'comparison'
    process = subprocess.run(
        [
            sys.executable,
            '-m',
            'fly_brain',
            'compare',
            '--first',
            str(first),
            '--second',
            str(second),
            '--duration-s',
            '0.1',
            '--trials',
            '1',
            '--output',
            str(output),
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )
    assert process.returncode == 0, process.stderr
    report = json.loads((output / 'pairwise_summary.json').read_text())[0]
    assert (report['spikes_a'], report['spikes_b'], report['timing_matches']) == (
        2,
        1,
        1,
    )
    assert (output / 'parity_rates.csv').is_file()


def test_comparison_writes_existing_report_filenames_without_overwriting(
    tmp_path: Path,
) -> None:
    output = tmp_path / 'comparison'
    result = ComparisonResult(
        {'timing_f1': 1.0}, ({'flywire_id': 10, 'rate_a_hz': 1.0},)
    )
    write_comparison(output, result)
    with (output / 'pairwise_summary.csv').open(newline='') as source:
        assert list(csv.DictReader(source)) == [{'timing_f1': '1.0'}]
    assert json.loads((output / 'pairwise_summary.json').read_text()) == [
        result.summary
    ]
    with pytest.raises(FileExistsError):
        write_comparison(output, result)

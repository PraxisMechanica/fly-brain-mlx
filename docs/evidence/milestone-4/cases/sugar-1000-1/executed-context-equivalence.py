import hashlib
import json
import re
import subprocess
from pathlib import Path

import numpy as np

root = Path.cwd()
legacy = root / 'docs/evidence/milestone-4/four-trial-memory'
current = (
    root
    / 'data/results/milestone-4-parity-sugar-1000-1-20261005-01/observations/paired-first'
)
a = json.loads((legacy / 'four-trial-memory.json').read_text())['trials'][1][
    'spike_context'
]
b = json.loads((current / 'causal.json').read_text())
assert (
    b['first_budget_violation'] is None
    and b['first_spike_step'] == 999
    and b['first_spike_neurons'] == [41514]
)
record = b['contexts']['spike']
assert record['neurons'] == a['neurons'] and b['contexts']['budget'] is None
mappings = {}
with (
    np.load(legacy / 'trial-1-spike-context.npz', allow_pickle=False) as old,
    np.load(current / 'spike-context.npz', allow_pickle=False) as new,
):
    for name in old.files:
        target = name.replace('_actual_leaf_', '_actual_mlx_leaf_').replace(
            '_native_reference_weights_si', '_reference_native_weight_si'
        )
        target = re.sub(
            r'_reference_path_(\d+)_delivered$',
            r'_reference_pathway_\1_delivered',
            target,
        )
        target = re.sub(
            r'_reference_path_(\d+)_(offset|slot_\d+)$',
            r'_reference_pathway_\1_queue_0_\2',
            target,
        )
        first, second = old[name], new[target]
        offset = name.endswith('_offset')
        assert first.dtype == second.dtype and first.tobytes() == second.tobytes(), name
        assert (
            (first.shape, second.shape) == ((1,), ())
            if offset
            else first.shape == second.shape
        ), name
        mappings[name] = {
            'singleton_field': target,
            'legacy_shape': list(first.shape),
            'singleton_shape': list(second.shape),
            'dtype': first.dtype.str,
            'sha256': hashlib.sha256(first.tobytes()).hexdigest(),
        }
    assert len(mappings) == 108
    assert new['affected_neuron_ids'].tolist() == [720575940620025620]
for historical, actual in zip(a['observations'], record['steps'], strict=True):
    snapshot = actual['actual_snapshot']
    assert historical['position'] == actual['position']
    for name in ('step', 'clock_step', 'source_cursor'):
        assert historical[name] == snapshot[name]
    assert float(historical['time_s']).hex() == snapshot['time_s_hex']
    assert historical['mlx_due_sha256'] == actual['mlx_due_mask_sha256']
result = {
    'checkpoint': subprocess.check_output(
        ['git', 'rev-parse', 'HEAD'], text=True
    ).strip(),
    'scope': 'First singleton execution context only; complete repeat, CPU metrics, and reviewed acceptance remain pending.',
    'case_accepted': False,
    'all_108_corresponding_native_context_arrays_equal': True,
    'only_shape_mapping': 'Legacy stored scalar int32 queue offsets in length-one arrays; singleton stores scalar shape. Native dtype and payload bytes remain identical.',
    'native_field_mappings': mappings,
    'current_previous_actual_snapshot_clocks_cursors_due_hashes_equal': True,
    'source_sha256': {
        str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in (
            legacy / 'trial-1-spike-context.npz',
            legacy / 'four-trial-memory.json',
            current / 'spike-context.npz',
            current / 'causal.json',
        )
    },
}
with (
    root / 'data/results/milestone-4-sugar1-first-cause-preflight-20261005-01.json'
).open('x') as f:
    json.dump(result, f, indent=2, allow_nan=False)
print(
    json.dumps(
        {
            'verified': True,
            'corresponding_native_arrays': len(mappings),
            'first_step': 999,
            'affected_neurons': [41514],
            'case_accepted': False,
        }
    )
)

import hashlib
import json

import numpy as np
import pytest
from pydantic import TypeAdapter

from fly_brain.simulation.observations import HostArray
from tests.support.session_proof_values import (
    BlockProof,
    proof_root,
    require_same_trial,
)


def require_array_bytes_equal(before: HostArray, after: HostArray) -> None:
    assert before.dtype == after.dtype and before.shape == after.shape
    assert before.tobytes() == after.tobytes()


@pytest.mark.integration
def test_retained_pinned_artifacts_prove_all_native_bytes_and_final_state(
    request: pytest.FixtureRequest,
) -> None:
    root = proof_root(request)
    adapter = TypeAdapter(list[BlockProof])
    ordinary = adapter.validate_json((root / 'ordinary/blocks.json').read_text())
    assert len(ordinary) == 32 and sum(block.rows for block in ordinary) == 1000
    compared = 0
    for mode in ('legacy', 'session', 'repeat', 'four-session'):
        actual = adapter.validate_json((root / mode / 'blocks.json').read_text())
        assert len(actual) == len(ordinary)
        for before, after in zip(ordinary, actual, strict=True):
            require_same_trial(before, after, 0)
            old_path = root / 'ordinary' / f'block-{before.begin:04d}.npz'
            new_path = root / mode / f'block-{after.begin:04d}.npz'
            assert (
                hashlib.sha256(old_path.read_bytes()).hexdigest()
                == before.artifact_sha256
            )
            assert (
                hashlib.sha256(new_path.read_bytes()).hexdigest()
                == after.artifact_sha256
            )
            with (
                np.load(old_path, allow_pickle=False) as old,
                np.load(new_path, allow_pickle=False) as new,
            ):
                for name in before.units:
                    require_array_bytes_equal(old[name], new[name][:, :1])
                    compared += 1
                for row in range(before.rows):
                    require_array_bytes_equal(old[f'due-{row}-0'], new[f'due-{row}-0'])
                    compared += 1
            end = before.begin + before.rows
            old_queue_path = root / 'ordinary' / f'queue-{end:04d}.npz'
            new_queue_path = root / mode / f'queue-{end:04d}.npz'
            assert (
                hashlib.sha256(old_queue_path.read_bytes()).hexdigest()
                == before.queue_artifact_sha256
            )
            assert (
                hashlib.sha256(new_queue_path.read_bytes()).hexdigest()
                == after.queue_artifact_sha256
            )
            with (
                np.load(old_queue_path, allow_pickle=False) as old,
                np.load(new_queue_path, allow_pickle=False) as new,
            ):
                require_array_bytes_equal(old['queue'], new['queue'][:, :1])
                compared += 1
    with (root / 'native-byte-comparison.json').open('x') as destination:
        json.dump(
            {
                'exact_native_arrays_compared': compared,
                'steps': 1000,
                'boundaries': 32,
                'slots_per_boundary': 19,
                'trial0_native_equality': True,
                'scope': 'Preservation only; no scientific acceptance',
            },
            destination,
            indent=2,
        )

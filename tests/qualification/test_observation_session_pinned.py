import hashlib
import importlib.metadata
import json
import os
from pathlib import Path

import mlx.core as mx
import numpy as np
import pytest

from fly_brain.infrastructure.seeded_random import uniforms
from fly_brain.simulation.experiments import EXPERIMENTS
from fly_brain.simulation.input_service import load_pinned_inputs
from fly_brain.simulation.inputs import file_sha256, load_connectome
from fly_brain.simulation.models import Stimulus
from fly_brain.simulation.stimulus_service import schedule
from tests.support.session_pinned import (
    record_mode,
)
from tests.support.session_proof_values import proof_root


def frozen_stimulus(root: Path, trials: tuple[int, ...]) -> Stimulus:
    with np.load(root / 'frozen-stimulus/stimulus.npz', allow_pickle=False) as saved:
        events = saved['events'][list(trials)]
    events.setflags(write=False)
    return Stimulus(events, (), (200.0,) * 21, trials, 20261004, 0, '')


@pytest.mark.integration
@pytest.mark.metal
@pytest.mark.parametrize(
    'mode', ('ordinary', 'legacy', 'session', 'repeat', 'four-session')
)
def test_complete_shortest_pinned_observation_preservation(
    mode: str, precision: str, request: pytest.FixtureRequest
) -> None:
    root = proof_root(request)
    project = os.environ.get('FLY_BRAIN_PINNED_PROJECT')
    if project is None:
        raise ValueError('Pinned proof requires an explicit read-only dataset root')
    connectome, pin = load_pinned_inputs(Path(project), lambda: load_connectome)
    trials = (0, 1, 2, 3) if mode == 'four-session' else (0,)
    generated = schedule(
        connectome, EXPERIMENTS['sugar'], 1000, trials, 20261004, draw_uniforms=uniforms
    )
    loaded = frozen_stimulus(root, trials)
    metadata = json.loads((root / 'frozen-stimulus/stimulus.json').read_text())
    assert metadata['shape'] == [4, 1000, 21] and metadata['dtype'] == '|u1'
    assert metadata['layout'] == ['trial', 'step', 'channel']
    assert metadata['trial_indices'] == [0, 1, 2, 3]
    assert metadata['seed_tuples'] == [[20261004, 0, trial] for trial in range(4)]
    assert metadata['generator'] == 'PCG64' and metadata['numpy'] == np.__version__
    assert metadata['dt_ms'] == 0.1 and metadata['seed'] == 20261004
    assert metadata['generator_code'] == metadata['experiment_code'] == 0
    assert metadata['targets'] == list(generated.targets)
    assert metadata['activated_ids'] == list(EXPERIMENTS['sugar'].activated_ids)
    assert metadata['rates_hz'] == list(generated.rates_hz)
    assert metadata['experiment'] == 'sugar' and metadata['silenced_ids'] == []
    assert metadata['input_sha256'] == {
        'completeness': pin.completeness_sha256,
        'connectivity': pin.connectivity_sha256,
    }
    assert loaded.events.dtype == np.uint8
    assert loaded.events.shape == (len(trials), 1000, 21)
    assert loaded.events.tobytes() == generated.events.tobytes()
    assert hashlib.sha256(loaded.events.tobytes()).hexdigest() == generated.sha256
    stimulus = Stimulus(
        loaded.events,
        generated.targets,
        generated.rates_hz,
        trials,
        generated.seed,
        generated.generator_code,
        generated.sha256,
    )
    recorder = record_mode(mode, connectome, stimulus, root / mode, precision)
    assert sum(proof.rows for proof in recorder.proofs) == 1000
    assert len(recorder.proofs) == 32 and recorder.proofs[-1].rows == 8
    assert tuple(proof.begin for proof in recorder.proofs) == tuple(range(0, 1000, 32))
    assert all(proof.trials == trials for proof in recorder.proofs)
    if mode != 'ordinary':
        assert all(
            proof.measured_checks and proof.checks_all for proof in recorder.proofs
        )
    source_root = Path(__file__).resolve().parents[2]
    with (root / mode / 'identity.json').open('x') as destination:
        json.dump(
            {
                'mode': mode,
                'device': mx.metal.device_info(),
                'MLX_ENABLE_TF32': precision,
                'compilation': 'disabled by unchanged bucketed preparation',
                'reduction': 'original compensated count tree; exact_counts=False',
                'versions': {
                    name: importlib.metadata.version(name)
                    for name in ('mlx', 'mlx-metal', 'numpy', 'pyarrow', 'pydantic')
                },
                'neurons': pin.neurons,
                'edges': pin.edges,
                'source_root': str(source_root),
                'source_sha256': {
                    str(path.relative_to(source_root)): file_sha256(path)
                    for path in sorted((source_root / 'src').rglob('*.py'))
                },
                'proof_source_sha256': {
                    name: file_sha256(source_root / name)
                    for name in (
                        'tests/qualification/test_observation_session_pinned.py',
                        'tests/support/session_pinned.py',
                    )
                },
                'trial_indices': trials,
                'input_sha256': [pin.completeness_sha256, pin.connectivity_sha256],
                'event_sha256': stimulus.sha256,
                'frozen_stimulus_metadata_sha256': file_sha256(
                    root / 'frozen-stimulus/stimulus.json'
                ),
                'frozen_stimulus_artifact_sha256': file_sha256(
                    root / 'frozen-stimulus/stimulus.npz'
                ),
                'steps': 1000,
                'elapsed_s': recorder.memory[-1].elapsed_s,
                'scope': 'Same-engine refactor preservation; no scientific acceptance',
            },
            destination,
            indent=2,
        )

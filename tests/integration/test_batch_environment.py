import hashlib
import json
from pathlib import Path

import pytest

from fly_brain.qualification.adapters.batch_environment import require_environments

pytestmark = pytest.mark.integration


@pytest.mark.parametrize(
    'fault',
    (
        'none',
        'missing',
        'version',
        'precision',
        'compile',
        'threads',
        'interop',
        'dtype',
        'device',
        'source_changed',
        'source_omitted',
        'launch_changed',
        'extra_source',
    ),
)
def test_batch_cannot_reuse_evidence_with_changed_execution_settings_or_source(
    tmp_path: Path, fault: str
) -> None:
    names = [
        'fly_brain.simulation.backend.core',
        'fly_brain.simulation.backend.arrays',
        'fly_brain.simulation.backend.engines',
        'fly_brain.simulation.backend.bucketed',
        'fly_brain.simulation.backend.accumulation',
        'fly_brain.simulation.backend.observation_session',
        'fly_brain.simulation.backend.reduction_evidence',
        'fly_brain.simulation.mapping',
        'fly_brain.simulation.models',
        'fly_brain.simulation.stimuli',
        'fly_brain.simulation.stimulus_service',
        'fly_brain.simulation.ports',
        'fly_brain.simulation.module',
        'fly_brain.simulation.experiments',
        'fly_brain.simulation.observations',
        'fly_brain.simulation.observation_ports',
        'fly_brain.simulation.observation_module',
        'fly_brain.qualification.models',
        'fly_brain.qualification.ports',
        'fly_brain.qualification.stimulus_ports',
        'fly_brain.qualification.session_observer',
        'fly_brain.qualification.session_expectations',
        'fly_brain.qualification.session_blocks',
        'fly_brain.qualification.causality',
        'fly_brain.qualification.adapters.active_cpu',
        'fly_brain.qualification.adapters.brian_jobs',
        'fly_brain.qualification.adapters.reference_build',
        'fly_brain.qualification.adapters.reference_native',
        'fly_brain.qualification.adapters.reference_queues',
        'fly_brain.qualification.adapters.observer_stream',
        'fly_brain.qualification.adapters.observer_evidence',
        'fly_brain.qualification.adapters.causal_capture',
        'fly_brain.qualification.adapters.causal_reduction',
        'fly_brain.qualification.adapters.paired_collect',
        'fly_brain.qualification.adapters.paired_observer',
        'fly_brain.qualification.adapters.paired_causes',
        'fly_brain.qualification.adapters.case_execution',
        'fly_brain.qualification.adapters.parity_case',
        'fly_brain.qualification.adapters.torch_reference',
        'fly_brain.qualification.adapters.torch_setup',
        'fly_brain.qualification.adapters.torch_observer',
        'fly_brain.qualification.adapters.torch_collect',
        'fly_brain.infrastructure.seeded_random',
    ]
    project = tmp_path / 'project'
    originals: dict[str, bytes] = {}
    hashes: dict[str, str] = {}
    for name in (*names, 'fly_brain.qualification.adapters.batch_extra'):
        path = project / 'src' / Path(*name.split('.')).with_suffix('.py')
        path.parent.mkdir(parents=True, exist_ok=True)
        data = ('recorded source ' + name).encode()
        path.write_bytes(data)
        originals[str(path.relative_to(project))] = data
        hashes[name] = hashlib.sha256(data).hexdigest()
    baseline = {
        'python': 'python',
        'platform': 'darwin',
        'versions': {
            'mlx': '0.32.3',
            'mlx-metal': '0.32.3',
            'numpy': '1.26.4',
            'brian2': '2.8.0',
            'torch': '2.11.0',
        },
        'MLX_ENABLE_TF32': '0',
        'compilation': 'disabled',
        'device': {
            'device_name': 'fixture',
            'max_recommended_working_set_size': 1,
            'memory_size': 1,
            'architecture': 'fixture',
            'max_buffer_length': 1,
            'resource_limit': 1,
        },
        'cpu_threads': 1,
        'cpu_interop_threads': 10,
        'cpu_default_dtype': 'torch.float32',
        'cpu_deterministic_algorithms': False,
        'scope': 'fixture',
        'source_sha256': {name: hashes[name] for name in names},
    }
    batch = tmp_path / 'batch'
    batch.mkdir()
    batch_data = json.loads(json.dumps(baseline))
    if fault == 'extra_source':
        batch_data['source_sha256']['fly_brain.qualification.adapters.batch_extra'] = (
            hashes['fly_brain.qualification.adapters.batch_extra']
        )
    (batch / 'environment.json').write_text(json.dumps(batch_data))
    singles: dict[int, tuple[Path, str]] = {}
    for trial in range(4):
        directory = tmp_path / f'single-{trial}'
        directory.mkdir()
        metadata = json.loads(json.dumps(baseline))
        if trial == 3:
            if fault == 'version':
                metadata['versions']['numpy'] = 'other'
            elif fault == 'precision':
                metadata['MLX_ENABLE_TF32'] = '1'
            elif fault == 'compile':
                metadata['compilation'] = 'enabled'
            elif fault == 'threads':
                metadata['cpu_threads'] = 2
            elif fault == 'interop':
                metadata['cpu_interop_threads'] = 1
            elif fault == 'dtype':
                metadata['cpu_default_dtype'] = 'torch.float64'
            elif fault == 'device':
                metadata['device']['architecture'] = 'other'
            elif fault == 'source_changed':
                metadata['source_sha256'][names[0]] = '0' * 64
            elif fault == 'source_omitted':
                del metadata['source_sha256'][names[0]]
        (directory / 'environment.json').write_text(json.dumps(metadata))
        singles[trial] = (
            directory,
            'changed' if trial == 3 and fault == 'launch_changed' else 'launch',
        )
    if fault == 'missing':
        del singles[3]

    def read_launch(commit: str, relative: str) -> bytes:
        return originals[relative] if commit == 'launch' else b'changed launch bytes'

    if fault in ('none', 'extra_source'):
        assert require_environments(
            project, (batch, 'launch'), singles, read_launch
        ) == {name: hashes[name] for name in names}
    else:
        with pytest.raises(ValueError):
            require_environments(project, (batch, 'launch'), singles, read_launch)

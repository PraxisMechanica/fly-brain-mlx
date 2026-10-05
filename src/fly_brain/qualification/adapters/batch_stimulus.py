import hashlib
from pathlib import Path
from typing import Literal, cast

import numpy as np
from numpy.typing import NDArray
from pydantic import BaseModel, ConfigDict

from fly_brain.simulation.models import Experiment, ExperimentName, InputPin, Stimulus


class _Metadata(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True, extra='forbid')
    format_version: Literal[1]
    layout: tuple[str, str, str]
    shape: tuple[int, int, int]
    dtype: Literal['|u1']
    dt_ms: float
    generator: Literal['PCG64']
    numpy: Literal['1.26.4']
    seed: int
    generator_code: int
    trial_indices: tuple[int, ...]
    targets: tuple[int, ...]
    activated_ids: tuple[int, ...]
    rates_hz: tuple[float, ...]
    experiment: ExperimentName
    experiment_code: int
    silenced_ids: tuple[int, ...]
    canonical_event_sha256: str
    per_trial_event_sha256: tuple[str, ...]
    seed_tuples: tuple[tuple[int, int, int], ...]
    input_sha256: dict[str, str]
    artifact_sha256: str


def load(directory: Path, experiment: Experiment, pin: InputPin) -> Stimulus:
    metadata = _Metadata.model_validate_json((directory / 'stimulus.json').read_text())
    artifact = directory / 'stimulus.npz'
    if hashlib.sha256(artifact.read_bytes()).hexdigest() != metadata.artifact_sha256:
        raise ValueError('Saved stimulus archive hash changed')
    with np.load(artifact, allow_pickle=False) as saved:
        if set(saved.files) != {'events'}:
            raise ValueError('Saved stimulus requires exactly its native event array')
        events = cast(NDArray[np.uint8], saved['events'])
    if (
        events.dtype != np.uint8
        or events.ndim != 3
        or events.shape != metadata.shape
        or events.shape[0] != len(metadata.trial_indices)
        or events.shape[1] < 1
        or events.shape[2] != len(metadata.targets)
        or len(metadata.targets) != len(experiment.activated_ids)
        or np.any(events > 1)
        or hashlib.sha256(events.tobytes()).hexdigest()
        != metadata.canonical_event_sha256
        or tuple(hashlib.sha256(row.tobytes()).hexdigest() for row in events)
        != metadata.per_trial_event_sha256
    ):
        raise ValueError(
            'Saved stimulus requires complete native bits and trial hashes'
        )
    if (
        metadata.layout != ('trial', 'step', 'channel')
        or metadata.dt_ms != 0.1
        or metadata.experiment != experiment.name
        or metadata.experiment_code != experiment.code
        or metadata.generator_code != experiment.generator_code
        or metadata.activated_ids != experiment.activated_ids
        or metadata.rates_hz != experiment.rates_hz
        or metadata.silenced_ids != experiment.silenced_ids
        or metadata.seed_tuples
        != tuple(
            (metadata.seed, metadata.generator_code, trial)
            for trial in metadata.trial_indices
        )
        or metadata.input_sha256
        != {
            'completeness': pin.completeness_sha256,
            'connectivity': pin.connectivity_sha256,
        }
    ):
        raise ValueError(
            'Saved stimulus provenance differs from its experiment or inputs'
        )
    events.setflags(write=False)
    return Stimulus(
        events,
        metadata.targets,
        metadata.rates_hz,
        metadata.trial_indices,
        metadata.seed,
        metadata.generator_code,
        metadata.canonical_event_sha256,
    )

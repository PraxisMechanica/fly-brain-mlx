import json
from collections.abc import Mapping
from pathlib import Path
from typing import cast

import numpy as np

from fly_brain.qualification.batch_evidence import (
    NativeDifference,
    NativeDigest,
    PhaseDifference,
    PhaseDigest,
    native_difference,
    phase_difference,
)

from .batch_native import Engine, NativeArrays, compare_final_trial


def mlx_phases(directory: Path, *, paired: bool) -> tuple[PhaseDigest, ...]:
    blocks: list[PhaseDigest] = []
    for line in (directory / 'phase-digests.jsonl').read_text().splitlines():
        row = json.loads(line)
        native = tuple(row['native_phase_sha256'])
        if paired:
            if len(native) != 2:
                raise ValueError(
                    'Singleton phase evidence requires both native engines'
                )
            native = (native[1],)
        blocks.append(
            PhaseDigest(
                row['begin'],
                row['rows'],
                native,
                tuple(row['mlx_queue_sha256']),
                tuple(tuple(due) for due in row['mlx_due_sha256']),
            )
        )
    return tuple(blocks)


def cpu_snapshots(directory: Path) -> tuple[NativeDigest, ...]:
    return tuple(
        NativeDigest(row['step'], tuple(row['native_sha256']))
        for row in (
            json.loads(line)
            for line in (directory / 'native-digests.jsonl').read_text().splitlines()
        )
    )


def compare(
    batch: Path,
    singletons: Mapping[int, Path],
    engine: Engine,
    steps: int,
    neurons: int,
    edges: int,
    channels: int,
) -> tuple[PhaseDifference | NativeDifference | None, dict[int, tuple[str, ...]]]:
    if set(singletons) != {0, 1, 2, 3}:
        raise ValueError(
            'Batch comparison requires independent trials zero through three'
        )
    if engine == 'mlx':
        difference = phase_difference(
            mlx_phases(batch, paired=False),
            {
                trial: mlx_phases(path, paired=True)
                for trial, path in singletons.items()
            },
            steps,
        )
    else:
        difference = native_difference(
            cpu_snapshots(batch),
            {trial: cpu_snapshots(path) for trial, path in singletons.items()},
            steps,
        )
    with np.load(batch / 'native.npz', allow_pickle=False) as archive:
        many = cast(NativeArrays, {name: archive[name] for name in archive.files})
    finals: dict[int, tuple[str, ...]] = {}
    for trial, path in singletons.items():
        filename = 'mlx-native.npz' if engine == 'mlx' else 'native.npz'
        with np.load(path / filename, allow_pickle=False) as archive:
            one = cast(NativeArrays, {name: archive[name] for name in archive.files})
        finals[trial] = compare_final_trial(
            many, one, engine, trial, neurons, edges, channels, steps
        )
    return difference, finals

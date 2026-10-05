import json
from pathlib import Path

import numpy as np


def verify(
    first: Path,
    repeat: Path,
    text_files: tuple[str, ...],
    array_files: tuple[str, ...],
) -> None:
    for filename in text_files:
        if (first / filename).read_bytes() != (repeat / filename).read_bytes():
            raise ValueError(f'Repeat evidence differs: {filename}')
    for filename in array_files:
        with (
            np.load(first / filename, allow_pickle=False) as a,
            np.load(repeat / filename, allow_pickle=False) as b,
        ):
            if set(a.files) != set(b.files):
                raise ValueError(f'Repeat native fields differ: {filename}')
            for name in a.files:
                one, two = a[name], b[name]
                if (one.dtype, one.shape, one.tobytes()) != (
                    two.dtype,
                    two.shape,
                    two.tobytes(),
                ):
                    raise ValueError(f'Repeat native array differs: {filename}/{name}')


def paired(first: Path, repeat: Path) -> None:
    summary = json.loads((first / 'causal.json').read_text())
    causes = tuple(
        label + '-context.npz'
        for label in ('budget', 'spike')
        if summary['contexts'][label] is not None
    )
    verify(
        first,
        repeat,
        (
            'phase-digests.jsonl',
            'physical-digests.jsonl',
            'reference-final-physical.json',
            'causal.json',
        ),
        (
            'reference-native.npz',
            'mlx-native.npz',
            'reference-final-physical.npz',
            *causes,
        ),
    )


def cpu(first: Path, repeat: Path) -> None:
    verify(first, repeat, ('native-digests.jsonl',), ('native.npz',))

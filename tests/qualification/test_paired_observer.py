from contextlib import closing
from pathlib import Path

import numpy as np
import pytest

from fly_brain.qualification.adapters.brian_jobs import build, run
from fly_brain.qualification.adapters.mlx_ledger import EventLedger
from fly_brain.qualification.adapters.mlx_observer import observe
from fly_brain.qualification.adapters.observer_stream import FinalSnapshot
from fly_brain.qualification.adapters.paired_observer import PairedBlock, pair_blocks
from fly_brain.qualification.adapters.reference_queues import ReferenceQueues
from fly_brain.simulation.backend import core
from fly_brain.simulation.backend.bucketed import prepare
from tests.qualification.test_mlx_observer import fixture

pytestmark = [pytest.mark.integration, pytest.mark.reference, pytest.mark.metal]


def test_live_engines_pair_every_phase_and_final_partial_block(
    precision: str, tmp_path: Path
) -> None:
    case = fixture()
    events = case.events[:1]
    job = build(case.connectome, case.targets, (3,), events[0], tmp_path / 'build')
    execution = prepare(case.connectome, case.targets, (3,), precision)
    mlx = observe(
        execution,
        core.initial_state(execution.network),
        events,
        EventLedger(case.connectome, case.targets, 1),
    )
    ledger = ReferenceQueues(case.connectome.sources, 6, events[0])
    with closing(run(job, tmp_path / 'results')) as reference:
        frames = tuple(pair_blocks(reference, mlx, ledger))
    blocks = [frame for frame in frames if isinstance(frame, PairedBlock)]
    assert [(block.reference.begin, block.reference.rows) for block in blocks] == [
        (0, 32),
        (32, 32),
        (64, 32),
        (96, 5),
    ]
    assert isinstance(frames[-1], FinalSnapshot) and ledger.step == 101
    for block in blocks:
        assert len(block.snapshots) == block.reference.rows
        assert block.reference.fields['pre_v'].dtype == np.float64
        assert block.mlx.fields['pre_v'].dtype == np.float32
        assert all(len(digest) == 64 for digest in block.native_sha256)

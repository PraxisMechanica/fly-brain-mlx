import gc
import tracemalloc
from pathlib import Path

import mlx.core as mx

from fly_brain.simulation.models import Connectome, Stimulus
from tests.support.session_proof_modes import (
    legacy_frames,
    ordinary_frames,
    session_frames,
)
from tests.support.session_proof_recorder import Recorder
from tests.support.session_proof_values import BlockProof as BlockProof
from tests.support.session_proof_values import NativeValue as NativeValue
from tests.support.session_proof_values import TrialProof as TrialProof
from tests.support.session_proof_values import require_same_trial as require_same_trial
from tests.support.session_proof_values import value_signature as value_signature


def record_mode(
    mode: str,
    connectome: Connectome,
    stimulus: Stimulus,
    output: Path,
    precision: str,
) -> Recorder:
    tracemalloc.start()
    mx.reset_peak_memory()
    recorder = Recorder(output, stimulus.trial_indices)
    recorder.sample('inputs-loaded-before-construction', 0)
    if mode == 'ordinary':
        frames = ordinary_frames(connectome, stimulus, recorder, precision)
    elif mode == 'legacy':
        frames = legacy_frames(connectome, stimulus, recorder, precision)
    elif mode in ('session', 'repeat', 'four-session'):
        frames = session_frames(connectome, stimulus, recorder, precision)
    else:
        raise ValueError('Unknown preservation execution mode')
    for frame in frames:
        recorder.sample('actual-yield-before-artifact-check', frame.begin + frame.rows)
        recorder.frame(frame)
        completed = frame.begin + frame.rows
        del frame
        gc.collect()
        recorder.sample('consumer-released-block', completed)
    recorder.sample('collector-complete', stimulus.events.shape[1])
    recorder.finish()
    tracemalloc.stop()
    return recorder

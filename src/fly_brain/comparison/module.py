from functools import partial

from .acceptance import evaluate_case, steps_from_reference_clock, validate_coordinates
from .commands import comparison
from .diagnostics import time_bin_counts
from .models import SpikeReader
from .pooling import measure_trials
from .ports import (
    CaseScoring,
    ComparisonCommand,
    ComparisonWriter,
    CoordinateValidation,
    ReferenceClockConversion,
    TimeBinCounting,
    TrialMeasurement,
)
from .reporting import compare_to_output
from .service import compare


def build_comparison(
    reader: SpikeReader, writer: ComparisonWriter
) -> ComparisonCommand:
    use_case = partial(
        compare_to_output, compare=partial(compare, reader=reader), write=writer
    )
    return partial(comparison, use_case=use_case)


def build_case_scoring() -> CaseScoring:
    return evaluate_case


def build_coordinate_validation() -> CoordinateValidation:
    return validate_coordinates


def build_reference_clock_conversion() -> ReferenceClockConversion:
    return steps_from_reference_clock


def build_trial_measurement() -> TrialMeasurement:
    return measure_trials


def build_time_bin_counting() -> TimeBinCounting:
    return time_bin_counts

from functools import partial

from .commands import comparison
from .models import SpikeReader
from .ports import ComparisonCommand, ComparisonWriter
from .reporting import compare_to_output
from .service import compare


def build_comparison(
    reader: SpikeReader, writer: ComparisonWriter
) -> ComparisonCommand:
    use_case = partial(
        compare_to_output, compare=partial(compare, reader=reader), write=writer
    )
    return partial(comparison, use_case=use_case)

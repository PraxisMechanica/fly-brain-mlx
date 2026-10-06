from pathlib import Path
from typing import Protocol

from .models import ComparisonRequest, ComparisonResult


class ComparisonUseCase(Protocol):
    def __call__(self, request: ComparisonRequest, /) -> ComparisonResult: ...


class ComparisonWriter(Protocol):
    def __call__(self, output: Path, result: ComparisonResult, /) -> None: ...


class ComparisonReport(Protocol):
    def __call__(
        self, request: ComparisonRequest, output: Path, /
    ) -> ComparisonResult: ...


class ComparisonCommand(Protocol):
    def __call__(self, request: ComparisonRequest, output: Path, /) -> int: ...

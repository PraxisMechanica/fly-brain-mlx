from dataclasses import dataclass
from typing import Literal, Protocol, TypeVar, overload


class ValueMetadata(Protocol):
    @property
    def shape(self) -> tuple[int, ...]: ...

    @property
    def ndim(self) -> int: ...

    @property
    def size(self) -> int: ...


class Float32Value(ValueMetadata, Protocol):
    @property
    def dtype(self) -> Literal['float32']: ...


class BooleanValue(ValueMetadata, Protocol):
    @property
    def dtype(self) -> Literal['bool']: ...


Float = TypeVar('Float', bound=Float32Value)
Boolean = TypeVar('Boolean', bound=BooleanValue, contravariant=True)


class Primitives(Protocol[Float, Boolean]):
    @overload
    def add(self, left: Float, right: int, /) -> Float: ...

    @overload
    def add(self, left: int, right: Float, /) -> Float: ...

    @overload
    def add(self, left: Float, right: Float, /) -> Float: ...

    def multiply(self, left: float, right: Float, /) -> Float: ...

    def where(self, mask: Boolean, first: Float, second: Float, /) -> Float: ...


def integrate(
    voltage_mv: Float,
    synaptic_mv: Float,
    available: Boolean,
    coefficients: tuple[float, float, float],
    *,
    primitives: Primitives[Float, Boolean],
) -> tuple[Float, Float]:
    a, b, c = coefficients
    voltage = primitives.add(
        primitives.add(-52, primitives.multiply(a, primitives.add(voltage_mv, 52))),
        primitives.multiply(c, synaptic_mv),
    )
    synaptic = primitives.multiply(b, synaptic_mv)
    return primitives.where(available, voltage, voltage_mv), primitives.where(
        available, synaptic, synaptic_mv
    )


@dataclass(frozen=True)
class FloatToken:
    name: str
    shape: tuple[int, ...] = (2,)
    ndim: int = 1
    size: int = 2
    dtype: Literal['float32'] = 'float32'


@dataclass(frozen=True)
class BooleanToken:
    name: str
    shape: tuple[int, ...] = (2,)
    ndim: int = 1
    size: int = 2
    dtype: Literal['bool'] = 'bool'


class Recorder:
    def __init__(self) -> None:
        self.calls: list[
            tuple[str, tuple[FloatToken | BooleanToken | int | float, ...]]
        ] = []

    @overload
    def add(self, left: FloatToken, right: int, /) -> FloatToken: ...

    @overload
    def add(self, left: int, right: FloatToken, /) -> FloatToken: ...

    @overload
    def add(self, left: FloatToken, right: FloatToken, /) -> FloatToken: ...

    def add(self, left: FloatToken | int, right: FloatToken | int, /) -> FloatToken:
        self.calls.append(('add', (left, right)))
        return FloatToken(f'r{len(self.calls)}')

    def multiply(self, left: float, right: FloatToken, /) -> FloatToken:
        self.calls.append(('multiply', (left, right)))
        return FloatToken(f'r{len(self.calls)}')

    def where(
        self, mask: BooleanToken, first: FloatToken, second: FloatToken, /
    ) -> FloatToken:
        self.calls.append(('where', (mask, first, second)))
        return FloatToken(f'r{len(self.calls)}')

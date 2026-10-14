import ast
from pathlib import Path

import pytest

from tests.quality.native_type_support import PACKAGE, query, write
from tests.quality.support import PROJECT
from tests.quality.test_reference_silencing_boundary import typed
from tests.support.numerical_value_contracts import (
    BooleanToken,
    FloatToken,
    Primitives,
    Recorder,
    integrate,
)
from tools.architecture.native_types import inspect_types

pytestmark = pytest.mark.unit
CONTRACT = PROJECT / 'tests/support/numerical_value_contracts.py'
CORE = PROJECT / 'src/fly_brain/simulation/backend/core.py'
COEFFICIENTS = (0.9950124621391296, 0.9801986813545227, 0.004937935154885054)
EXPRESSION = """a, b, c = COEFFICIENTS
with mx.stream(mx.gpu):
    voltage = -52 + a * (voltage_mv + 52) + c * synaptic_mv
    synaptic = b * synaptic_mv
    return mx.where(available, voltage, voltage_mv), mx.where(available, synaptic, synaptic_mv)
"""
CONSTANTS = """DT_MS = 0.1
_a = math.exp(-DT_MS / 20)
COEFFICIENTS = tuple(float(np.float32(value)) for value in (_a, math.exp(-DT_MS / 5), _a * -math.expm1(-DT_MS * (1 / 5 - 1 / 20)) / 3))
"""
NATIVE = """from contract import Float32Value, BooleanValue, Primitives, integrate
from provider import FloatToken, BooleanToken, Recorder
voltage = FloatToken('v')
synaptic = FloatToken('g')
mask = BooleanToken('available')
primitives: Primitives[FloatToken, BooleanToken] = Recorder()
float_value: Float32Value = voltage
boolean_value: BooleanValue = mask
result = integrate(voltage, synaptic, mask, (0.5, 0.25, 0.125), primitives=primitives)
"""


def sources(code: str) -> dict[str, str]:
    source = CONTRACT.read_text()
    tree = ast.parse(source)
    providers = '\n'.join(ast.unparse(node) for node in tree.body[-3:])
    function = next(node for node in tree.body if isinstance(node, ast.FunctionDef))
    contract = ''.join(source.splitlines(keepends=True)[: function.end_lineno]).replace(
        'from dataclasses import dataclass\n', ''
    )
    return {
        'contract.py': contract,
        'provider.py': 'from dataclasses import dataclass\nfrom typing import Literal, overload\n'
        + providers,
        'consumer.py': NATIVE + code,
    }


def check(root: Path, files: dict[str, str], status: int, *diagnostics: str) -> None:
    for name, source in files.items():
        (root / name).write_text(source)
    result, output = typed(root, files['consumer.py'])
    assert (result, all(item in output for item in diagnostics)) == (status, True), (
        output
    )


def expression(source: str) -> str:
    tree = ast.parse(source)
    function = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == 'integrate'
    )
    return ast.dump(ast.Module(body=function.body, type_ignores=[]))


def test_native_provider_closure_bounds_and_shared_repair(tmp_path: Path) -> None:
    module = 'tests.support.numerical_value_contracts'
    code = NATIVE.replace('from contract import', f'from {module} import').replace(
        'from provider import', f'from {module} import'
    )
    files = {'consumer.py': code + 'closed: tuple[FloatToken, FloatToken] = result\n'}
    check(tmp_path, files, 0)
    observed = inspect_types(
        tmp_path,
        write(tmp_path, files),
        (
            query(tmp_path, 'consumer.py', 9, 'result'),
            query(tmp_path, 'consumer.py', 9, 'integrate'),
        ),
        PACKAGE,
        extra_paths=(PROJECT,),
    )
    result, function = (observed.type_at(site) for site in observed.sites)
    assert [
        (observed.types[item.type].name, item.unbounded)
        for item in result.tuple_arguments
    ] == [(module + '.FloatToken', False)] * 2
    for index, kind in ((0, 'Float32Value'), (2, 'BooleanValue')):
        parameter_type = function.parameters[index].type
        assert parameter_type is not None
        bound = observed.types[parameter_type].bound
        assert bound is not None and observed.types[bound].name == module + '.' + kind
    assert (
        function.declaration is not None
        and function.declaration.location.path == str(CONTRACT)
    )
    for site in observed.sites:
        observed.require_precise(site)


@pytest.mark.parametrize(
    'code,rule',
    (
        (
            'from mlx.core import array\ndef vendor(value: array) -> None:\n    integrate(value, synaptic, mask, (0.5, 0.25, 0.125), primitives=primitives)\n',
            'reportArgumentType',
        ),
        (
            'from mlx.core import array\nvendor: Primitives[array, BooleanToken]\n',
            'reportInvalidTypeArguments',
        ),
        (
            'from typing import TypeVar\nUnbounded = TypeVar("Unbounded")\ndef loose(value: Primitives[Unbounded, BooleanToken]) -> Primitives[Unbounded, BooleanToken]:\n    return value\n',
            'reportInvalidTypeArguments',
        ),
        (
            'wrong: Primitives[BooleanToken, BooleanToken] = Recorder()\n',
            'reportInvalidTypeArguments',
        ),
        ('primitives.where(voltage, voltage, synaptic)\n', 'reportArgumentType'),
        ('primitives.add(voltage, 52.0)\n', 'reportCallIssue'),
        ('primitives.multiply("0.5", voltage)\n', 'reportArgumentType'),
        ('primitives.add(1, 2)\n', 'reportCallIssue'),
        ('wrong: tuple[BooleanToken, BooleanToken] = result\n', 'reportAssignmentType'),
        ('float_value.shape = (3,)\n', 'reportAttributeAccessIssue'),
        ('boolean_value.dtype = "bool"\n', 'reportAttributeAccessIssue'),
    ),
)
def test_native_rejects_non_neutral_wrong_kind_and_mutable_surfaces(
    tmp_path: Path, code: str, rule: str
) -> None:
    check(tmp_path, sources(code), 1, 'consumer.py:', rule)


@pytest.mark.parametrize(
    'kind,original,replacement',
    (
        ('Unbounded, BooleanToken', "'Float', bound=Float32Value", "'Float'"),
        ('FloatToken, Unbounded', 'bound=BooleanValue, ', ''),
    ),
    ids=('float', 'boolean'),
)
def test_removing_each_actual_bound_loses_its_same_rejection(
    tmp_path: Path, kind: str, original: str, replacement: str
) -> None:
    code = (
        'from typing import TypeVar\nUnbounded = TypeVar("Unbounded")\ndef use(value: Primitives['
        + kind
        + ']) -> Primitives['
        + kind
        + ']:\n    return value\n'
    )
    files = sources(code)
    check(tmp_path, files, 1, 'reportInvalidTypeArguments')
    files['contract.py'] = files['contract.py'].replace(original, replacement)
    check(tmp_path, files, 0)


def typed_calls(
    calls: list[tuple[str, tuple[FloatToken | BooleanToken | int | float, ...]]],
) -> list[
    tuple[
        str,
        tuple[
            tuple[
                type[FloatToken | BooleanToken | int | float],
                FloatToken | BooleanToken | int | float,
            ],
            ...,
        ],
    ]
]:
    return [
        (name, tuple((type(value), value) for value in operands))
        for name, operands in calls
    ]


def test_integrate_keeps_eight_ordered_calls_and_actual_scalar_kinds() -> None:
    voltage, synaptic, available = (
        FloatToken('v'),
        FloatToken('g'),
        BooleanToken('available'),
    )
    recorder = Recorder()
    primitives: Primitives[FloatToken, BooleanToken] = recorder
    result = integrate(
        voltage, synaptic, available, COEFFICIENTS, primitives=primitives
    )
    a, b, c = COEFFICIENTS
    expected: list[tuple[str, tuple[FloatToken | BooleanToken | int | float, ...]]] = [
        ('add', (voltage, 52)),
        ('multiply', (a, FloatToken('r1'))),
        ('add', (-52, FloatToken('r2'))),
        ('multiply', (c, synaptic)),
        ('add', (FloatToken('r3'), FloatToken('r4'))),
        ('multiply', (b, synaptic)),
        ('where', (available, FloatToken('r5'), voltage)),
        ('where', (available, FloatToken('r6'), synaptic)),
    ]
    assert (typed_calls(recorder.calls), result) == (
        typed_calls(expected),
        (FloatToken('r7'), FloatToken('r8')),
    )


def test_actual_core_expression_constants_and_scalar_weakening() -> None:
    source = CORE.read_text()
    expected = ast.dump(ast.parse(EXPRESSION))
    assert expression(source) == expected
    tree = ast.parse(source)
    constant_names = {'DT_MS', '_a', 'COEFFICIENTS'}
    selected: list[ast.stmt] = [
        node
        for node in tree.body
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id in constant_names
            for target in node.targets
        )
    ]
    assert ast.dump(ast.Module(body=selected, type_ignores=[])) == ast.dump(
        ast.parse(CONSTANTS)
    )
    changed = source.replace('(voltage_mv + 52)', '(voltage_mv + 52.0)')
    assert expression(changed) != expected
    assert (
        expression(changed).replace('Constant(value=52.0)', 'Constant(value=52)')
        == expected
    )

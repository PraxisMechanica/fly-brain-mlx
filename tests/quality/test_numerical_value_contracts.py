import ast

from tests.quality.support import PROJECT

CORE = PROJECT / 'src/fly_brain/simulation/backend/core.py'

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


def expression(source: str) -> str:
    tree = ast.parse(source)
    function = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == 'integrate'
    )
    return ast.dump(ast.Module(body=function.body, type_ignores=[]))


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

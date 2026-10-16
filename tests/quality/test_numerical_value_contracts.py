import ast

from tests.quality.support import PROJECT

CORE = PROJECT / 'src/fly_brain/simulation/backend/core.py'

CONSTANTS = """DT_MS = 0.1
_a = math.exp(-DT_MS / 20)
COEFFICIENTS = tuple(float(np.float32(value)) for value in (_a, math.exp(-DT_MS / 5), _a * -math.expm1(-DT_MS * (1 / 5 - 1 / 20)) / 3))
VOLTAGE_INCREMENT = float(np.float32(math.expm1(-DT_MS / 20)))
SYNAPTIC_INCREMENT = float(np.float32(math.expm1(-DT_MS / 5)))
"""


def constants(source: str) -> str:
    tree = ast.parse(source)
    constant_names = {
        'DT_MS',
        '_a',
        'COEFFICIENTS',
        'VOLTAGE_INCREMENT',
        'SYNAPTIC_INCREMENT',
    }
    selected: list[ast.stmt] = [
        node
        for node in tree.body
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id in constant_names
            for target in node.targets
        )
    ]
    return ast.dump(ast.Module(body=selected, type_ignores=[]))


def test_core_constants_preserve_host_construction_and_float32_precision() -> None:
    source = CORE.read_text()
    expected = ast.dump(ast.parse(CONSTANTS))
    assert constants(source) == expected
    for precision in ('float16', 'float64'):
        assert constants(source.replace('np.float32', f'np.{precision}')) != expected

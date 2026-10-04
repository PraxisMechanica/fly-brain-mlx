import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption('--artifact-output', help='Fresh qualification artifact directory')

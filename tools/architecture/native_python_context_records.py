"""Immutable canonical native Python context observations."""

from typing import Literal

from pydantic import Field, field_validator

from tools.architecture.policy import Digest, Record


class ContextInput(Record):
    path: str
    sha256: Digest


class ContextEnvironment(Record):
    root: str
    python: Literal['3.10']
    platform: str
    extra_paths: tuple[str, ...]
    import_roots: tuple[str, ...]


class ContextOrigin(ContextInput):
    raw_uri: str
    module: str
    mapped: bool
    typeshed: bool
    third_party: bool
    py_typed: bool


class NativePythonContextReport(Record):
    schema_version: Literal[1] = Field(alias='schema')
    version: Literal['1.1.414']
    node_version: str
    host_kind: Literal[0]
    request_sha256: Digest
    configuration: tuple[ContextInput, ...]
    primary_config: str
    diagnostic_rules: tuple[tuple[str, str | bool], ...]
    include: tuple[tuple[str, str], ...]
    exclude: tuple[tuple[str, str], ...]
    ignore: tuple[tuple[str, str], ...]
    environments: tuple[ContextEnvironment, ...]
    venv: str | None
    venv_path: str | None
    stub_path: str
    configured_typeshed: str | None
    tracked: tuple[str, ...]
    stub_inputs: tuple[str, ...]
    sources: tuple[ContextInput, ...]
    loaded: tuple[ContextOrigin, ...]
    read_inputs: tuple[ContextInput, ...]
    bridge_sources: tuple[ContextInput, ...]
    compiler_artifacts: tuple[ContextInput, ...]
    missing: tuple[str, ...]

    @field_validator('schema_version', 'host_kind', mode='before')
    @classmethod
    def exact_schema(cls, value: object) -> object:
        if type(value) is not int:
            raise ValueError('unsupported context schema')
        return value

    def require(self, capability: str) -> None:
        if capability not in (
            'configuration',
            'source_selection',
            'loaded_source_origins',
        ):
            raise ValueError('COV002: native Python context lacks ' + capability)

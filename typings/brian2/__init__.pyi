from collections.abc import Mapping, Sequence
from typing import Any, TypeAlias

Quantity: TypeAlias = Any
mV: Quantity
ms: Quantity
Hz: Quantity
__version__: str

class BrianObject: ...

class CodeRunner:
    active: bool
    abstract_code: str

class Variable:
    dtype: object

class NeuronGroup(BrianObject):
    v: Quantity
    g: Quantity
    rfc: Quantity
    lastspike: Quantity
    not_refractory: Any
    state_updater: CodeRunner
    resetter: dict[str, CodeRunner]
    variables: dict[str, Variable]
    def __init__(
        self,
        N: int,
        model: str,
        *,
        method: str,
        refractory: str,
        namespace: Mapping[str, Any],
        threshold: str | None = None,
        reset: str | None = None,
        name: str | None = None,
    ) -> None: ...
    def __getitem__(self, key: int) -> NeuronGroup: ...

class SynapticPathway:
    name: str
    order: int

class Synapses(BrianObject):
    variables: dict[str, Variable]
    w: Quantity
    delay: Quantity
    pre: SynapticPathway
    def __init__(
        self,
        source: BrianObject,
        target: NeuronGroup,
        model: str = '',
        *,
        on_pre: str,
        delay: Quantity = ...,
        name: str | None = None,
    ) -> None: ...
    def connect(self, *, i: Any = ..., j: Any = ...) -> None: ...

class PoissonInput(BrianObject):
    def __init__(
        self,
        target: NeuronGroup,
        target_var: str,
        *,
        N: int,
        rate: Quantity,
        weight: Quantity,
    ) -> None: ...

class SpikeGeneratorGroup(BrianObject):
    variables: dict[str, Variable]
    def __init__(
        self, N: int, indices: Any, times: Quantity, *, name: str | None = None
    ) -> None: ...

class StateMonitor(BrianObject):
    variables: dict[str, Variable]
    t: Quantity
    v: Quantity
    g: Quantity
    lastspike: Quantity
    not_refractory: Any
    def __init__(
        self,
        source: NeuronGroup,
        variables: str | Sequence[str],
        *,
        record: bool,
        when: str,
        order: int = 0,
        name: str | None = None,
    ) -> None: ...

class SpikeMonitor(BrianObject):
    variables: dict[str, Variable]
    i: Any
    t: Quantity
    def __init__(self, source: NeuronGroup, *, name: str | None = None) -> None: ...

class Network:
    name: str
    def __init__(self, *objects: BrianObject, name: str | None = None) -> None: ...
    def run(self, duration: Quantity) -> None: ...
    def scheduling_summary(self) -> object: ...

class Clock:
    dt: Quantity
    variables: dict[str, Variable]

defaultclock: Clock

class CodeGeneration:
    target: str

class StandalonePreferences:
    extra_make_args_unix: list[str]
    openmp_threads: int

class DevicePreferences:
    cpp_standalone: StandalonePreferences

class Preferences:
    as_file: str
    codegen: CodeGeneration
    devices: DevicePreferences

prefs: Preferences

class Device:
    headers: list[str]
    libraries: list[str]
    def reinit(self) -> None: ...
    def build(
        self, *, directory: str, clean: bool, with_output: bool, run: bool = True
    ) -> None: ...
    def get_array_filename(self, variable: Variable) -> str: ...
    def get_array_name(
        self, variable: Variable, *, access_data: bool = True
    ) -> str: ...
    def insert_code(self, slot: str, code: str) -> None: ...

device: Device

def start_scope() -> None: ...
def set_device(name: str, *, build_on_run: bool = ...) -> None: ...

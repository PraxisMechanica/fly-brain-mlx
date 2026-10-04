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
    order: int

class Synapses(BrianObject):
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
    def __init__(
        self, N: int, indices: Any, times: Quantity, *, name: str | None = None
    ) -> None: ...

class StateMonitor(BrianObject):
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
    ) -> None: ...

class SpikeMonitor(BrianObject):
    i: Any
    t: Quantity
    def __init__(self, source: NeuronGroup) -> None: ...

class Network:
    def __init__(self, *objects: BrianObject) -> None: ...
    def run(self, duration: Quantity) -> None: ...
    def scheduling_summary(self) -> object: ...

class Clock:
    dt: Quantity

defaultclock: Clock

class CodeGeneration:
    target: str

class StandalonePreferences:
    extra_make_args_unix: list[str]

class DevicePreferences:
    cpp_standalone: StandalonePreferences

class Preferences:
    codegen: CodeGeneration
    devices: DevicePreferences

prefs: Preferences

class Device:
    def reinit(self) -> None: ...
    def build(self, *, directory: str, clean: bool, with_output: bool) -> None: ...

device: Device

def start_scope() -> None: ...
def set_device(name: str, *, build_on_run: bool = ...) -> None: ...

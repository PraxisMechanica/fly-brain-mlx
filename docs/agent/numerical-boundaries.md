# Numerical implementation boundaries

Audience: agents. Reviewed 2026-10-13 by a fresh GPT-6 Astra review at `xhigh`,
against `9d73531edb2f9974cfeda1623348239401529bc6`. The coordinator checked the
source declarations and all four frozen hashes. No numerical changes or
scientific executions were made for this review.

The [ownership contract](architecture-ownership.md) requires exact source hashes
for two adapted references and two legacy observation oracles. Their hashes and
lineage have one owner: [ownership.json](../../tools/architecture/ownership.json).
The active scope and holds remain in [milestone.md](../../milestone.md).

## Conflict with complete separation

Keeping these four sources byte exact is incompatible with complete separation
of owned model rules and provider implementations under the strict profile.
Moving a mixed file into an integration preserves its bytes but keeps model
policy in the provider. An opaque session wrapper preserves the same internal
responsibilities. Neither constitutes a complete repair.

| Source | Exact responsibility that needs separation |
| --- | --- |
| [torch_reference.py](../../src/fly_brain/qualification/adapters/torch_reference.py) | `model_parameters`, `AlphaSynapse`, `LIFNeuron`, `AlphaLIF`, and `TorchModel` combine model defaults/transitions with tensors, `nn.Module`, and autograd. Domain placement fails OWN005; provider placement retains OWN006. Framework inheritance also requires COMP001 analysis. |
| [brian_reference.py](../../src/fly_brain/qualification/adapters/brian_reference.py) | `default_parameters`, `add_poisson_inputs`, and `silence_neurons` contain independent equations, refractory choices, and silencing with Brian quantities and objects. They combine qualification rules and provider mechanics. |
| [legacy_mlx_observer.py](../../tests/support/legacy_mlx_observer.py) and [legacy_mlx_ledger.py](../../tests/support/legacy_mlx_ledger.py) | These system-test oracles import the current backend paths and consume raw device fields. A neutral replacement cannot preserve those bindings automatically. Re-exporting vendor implementations through the old domain paths retains the forbidden source/type dependence. |

[engines.py](../../src/fly_brain/simulation/backend/engines.py)'s `Advance` exposes
`core.State`, `core.StepTrace`, and `mx.array`. Renaming it to a protocol with the
same members does not repair DEP004. The recorded ROLE006 finding also needs its
literal public-contract scope checked before it is retired. The existing six
findings are not a complete analysis or a sufficient blanket deviation list.

## Smallest sound implementation boundary

Simulation owns model constants, preparation rules, state transitions, queue
semantics, and the selected reducers. Qualification owns independent reference
semantics, setup interpretation, and observation requirements. Provider
integrations own device representation, conversion, streams/evaluation, framework
objects, compilation, and process lifecycle.

Keep the existing [observation ports](../../src/fly_brain/simulation/observation_ports.py)
and application-facing executor contract. No second universal engine interface
is needed. Non-frozen host preparation and observation shells can be separated
without changing the frozen sources, but that does not clear the inner findings.

After resolving the freeze, the inner rules need a checked read-only numerical
value contract and only the primitive operations actually consumed. Provider
code must implement those primitives, rather than the model or reducer itself.
Opaque `object` values, casts, a generic operation dispatcher, or an adapter
calling a domain rule cannot supply the required purity and ownership evidence.

Complete separation therefore needs a human amendment permitting structural
changes to the adapted reference modules and affected legacy imports/interfaces,
while preserving independent scientific lineage and numerical behavior. If byte
identity remains mandatory, exact human-approved rule/symbol deviations must stay
reported. Neither option grants a clean result to incomplete 37-rule analysis.
No amendment or deviation has been approved by this review.

## Preservation required for a repair

The [numerical contract](numerical-contract.md) owns equations, order, precision,
state/event/queue behavior, and acceptance. Preserve the pinned inputs and seven
independent fixtures. Keep the four current source hashes until the freeze is
explicitly resolved.

Kernel/value changes require the existing complete reference/core/factored suite,
157 scalar cases, and affected layout checks against fresh independent references.
Observation changes require the existing transparency, fault, queue, repeat,
chunk, and standalone/batch consumers. Torch shell changes compare all five
native tensors; Brian changes preserve generated numerical code, inputs,
initialization, schedule, build settings, and failure handling. Update every
actual source-identity dependency and retain omission/change rejection tests.

The legacy MLX oracles share the current kernel. Their equality proves observation
transparency, not independent preservation of changed kernel arithmetic. These
checks authorize no numerical remedy, new execution mode, full-network matrix,
or performance work. Full architecture status remains ANALYSIS FAILED until
all required resolving mechanisms and predicates are implemented and executed.

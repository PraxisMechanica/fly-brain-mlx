# Numerical implementation boundaries

Audience: agents. The [numerical contract](numerical-contract.md) owns scientific
acceptance; [project architecture policy](architecture-policy.md) owns practical
structure; [milestone.md](../../milestone.md) owns current work.

## Accepted implementation boundaries

Production is MLX-only. Backend code may directly use MLX arrays, native state,
traces, streams, compilation and existing numerical operations. Independent
qualification references may define their models through Brian2/PyTorch and use
legitimate framework inheritance. No provider-neutral tensor interface, numerical
primitive dispatcher, or model/provider rewrite is required for portability.

Keep useful application-facing observation contracts. Simplifying composition or
removing a pass-through getter should preserve the actual callback, arguments,
loading/initialization order, outputs and failures rather than introduce a second
implementation. Numerical expressions and array operations need no new wrapper.

## Protected source identity and independent lineage

The [source guard](architecture-ownership.md) names the three independent reference sources.
Keep their current reviewed hashes unless a specific authorized structural repair
has verified scientific preservation, independent lineage and all source-identity
consumers. Do not rebaseline a hash to silence a check.

The extracted reference parameter factory and remaining Torch source have separate
hash guards and original lineage. Brian2 is an independent reference. Direct MLX
observation comparisons establish transparency, not independent preservation of
changed kernel arithmetic.
Preserve pinned FlyWire inputs and the seven independent regression fixtures.

## Verification required for actual numerical changes

| Changed behavior | Required preservation evidence |
| --- | --- |
| Kernel arithmetic or numerical values | Existing reference/core/factored checks, 157 scalar cases and affected layout checks against fresh independent references; unchanged equations, order, precision and discrete state |
| Observation behavior | Affected transparency, fault, queue, repeat, chunk and standalone/batch consumers |
| Torch reference execution | All five native tensors and existing independent reference checks |
| Brian reference execution | Generated numerical code, inputs, initialization, schedule, build settings and failure handling |
| Producer source dependencies | Every actual source-identity consumer and existing omission/change rejection cases |

Use the automatic affected-test boundaries for ordinary changes. Scientific
checks follow the affected numerical behavior. Any new arithmetic, representation
or execution mode
still needs the qualification required by the numerical contract; source structure
or mathematical equivalence alone is insufficient.

The numerical contract owns full-network acceptance.

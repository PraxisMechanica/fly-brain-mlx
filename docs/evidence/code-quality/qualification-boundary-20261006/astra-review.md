# Prospective qualification boundary review

Reviewer: `/root/review_qualification_boundary`, fresh-context `gpt-6-astra` at
`xhigh`. Reviewed checkpoint `23dac175679b8cbc6b102c4ecc143e9a85a34487`.
Confidence: 94%. Read-only source review; no tests, simulations, or database
operations were run by the reviewer. The parent retains implementation and
verification ownership.

## Decision and source findings

Qualification owns independent expectation history and acceptance. Simulation
exposes opaque execution capabilities and neutral observations of actual native
state. A simulator-issued acceptance result cannot replace independent checks.

`paired_collect.py` constructs concrete simulation state and consumes its
network. `mlx_observer.py` consumes concrete execution/state/trace objects and
mixes collection, device operations, and qualification checks. `paired_causes.py`
recovers `Layout` through `cast(partial, execution.advance).args[1]`, which its
execution contract does not promise. `causal_reduction.py` correctly reads actual
ordered device leaves; reconstructing them from host input would weaken causal
proof. Type-only `HostArray` imports also reach the MLX backend. These are
resolved source findings, not a completed 37-rule compliance result.

`EventLedger` contains scientific expectation policy: refractory availability,
strict thresholding, due-event history, accepted/discarded events, input gates,
last-spike clocks, finiteness, and all nineteen physical queue slots. Keep this
policy in qualification. Its receiving expectation must use qualification's
independently calculated spike predicate, rather than candidate claims.

## Minimal capabilities

Use qualification-owned typed factory/session/evidence-reader ports. Keep
`Network`, `State`, `StepTrace`, `Layout`, device arrays, streams, evaluation, and
closure representation opaque. Fresh repeats receive fresh sessions. Neutral
facts retain every current phase field, native dtype/shape/units/trial order,
actual due identities/digests, every boundary queue digest, and the complete final
actual queue. Host observations require detached, read-only ownership.

A reduction-row reader returns actual target identity, ordered original edge
IDs, native float32 counts, occupied padding, and truthful bound reduction mode.
Qualification pairs those leaves with the independent original Brian2 weights.

The large physical-queue comparison can remain on the device behind a narrow
read-only capability. Qualification supplies its independent original-edge
maps, source histories, and receiving expectations. The provider may gather and
compare every actual entry; it must not calculate threshold, refractory, delay,
history, tolerance, or acceptance policy. Missing evidence and comparison
failures propagate. This avoids retaining nineteen full queue histories while
preserving complete coverage.

Simulation's module constructs its implementation; qualification's module
constructs its ledger/capture services; global composition wires public ports.
Global composition does not perform the case workflow.

## Verification and adoption limits

A faithful type/forwarding seam requires source/behavior preservation and actual
neutral field/leaf checks, including detached ownership, duplicates, silencing,
zero-degree targets, and padding. Preserve core coefficients, operation order,
queue transitions, inputs, precision/compilation, and reference source/build
settings. No arithmetic/execution-mode change is authorized by this review.

Changing ledger policy, native extraction/comparison, or observation/evaluation
scheduling additionally requires fresh observer transparency and integrity:
ordinary/observed exact native phases, due masks, physical queues, spikes and
final state; blocks 1/17/32 and partial blocks; chunk continuation; fresh repeats;
actual four-trial/singleton comparisons; every current discrete fault and each
queue slot; nonfinite states, missing/reordered frames, corrupted mappings and
wrong/omitted comparison operands; causal contexts crossing a block boundary.
Before replacing the full-network collector, qualify the complete shortest
pinned-network ordinary/observed/repeated proof and bounded concurrent memory.
Keep the prescribed one-second batch obligations, including all 313 MLX blocks.

Architecture rejection fixtures must cover direct, aliased, type-only,
transitive, re-exported, captured, and factory-return implementation leaks. No
broad qualification exemption. Missing mechanisms remain ANALYSIS FAILED.

The concrete future comparator and its performance are unverified. This review
does not reproduce archived array proofs, qualify reference reuse, or complete
application compliance. A preserved boundary grants zero new case acceptances;
the existing 9/52 original-mode scope and failed one-second sugar F1 remain.

## Parent verification and next action

The parent opened the actual case/paired collection, observer, ledger, causal
writer/leaf-reader, engine/array/layout, and retained evidence-design sources.
It confirms the closure introspection, actual native leaf reads, thirty ledger
checks, 19 physical slots, and the need for independent expectations. The parent
accepts this prospective decision with the above limits.

First implement neutral reduction evidence values and a typed actual-row reader,
removing closure introspection without changing stepping/ledger scheduling.
Verify native bytes and immutable ownership before delivery. Then build the
opaque fresh-run/session and independent expectation/comparison slice; require
its complete transparency qualification before adoption. Structural coverage
remains incomplete until all leaking callers and mandatory mechanisms are fixed.

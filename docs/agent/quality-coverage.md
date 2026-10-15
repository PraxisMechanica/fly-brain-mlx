# Quality enforcement coverage

The project gate implements the practical architecture policy. It does not
certify every semantic property or grant scientific acceptance.

| Mechanism | Scope |
| --- | --- |
| Ruff, strict Pyright | Changed Python and affected type consumers; third-party limits remain documented. |
| Import contracts | Production/reference, comparison/execution and configured input/observation boundaries. |
| Scientific identity | Five protected sources and reviewed provenance; missing or changed protected bytes fail. |
| Indexed inputs | Required source/configuration/tool inputs must be indexed. |
| Documentation budget | All tracked documentation formats share a 10,000-word maximum. |
| Affected tests | One automatic invocation at commit and CI; no push/manual replay. |
| Native metrics | Qualified calculations and per-blob identity reuse; numerical CQ001–CQ003 findings are advisory. |

Missing tools, parse errors, malformed results, invalid inputs and unsupported
required scope still fail. First-party forbidden targets must exist, including
when the corresponding source scope is inactive. Python removals conservatively
widen static scope; native/process/resource consumers require explicit focused
verification where import facts are insufficient.

Commit metrics check the index; push/CI cover submitted commits and merge parents.
Calculation/import facts may be reused under their validated identities; test or
quality verdicts are not persistently cached. Metric provenance and exact authored
patches remain indexed. Whole-file scores are not complete architecture proofs.

The semantic registry, compiler bridge, universal role/alias/effect analyzer and
neutral tensor prototype are retired. Do not recreate them. Concrete MLX backend
contracts and recognizable independent reference models are permitted. Existing
state/identity/lifecycle boundaries still require meaningful source review and
behavior tests. Scientific rules remain in `numerical-contract.md`, source
lineage in `architecture-ownership.md`, and execution policy in `development.md`.

# MLX fly-brain backend

Workspace for an Apple MLX backend for the [Eon Systems fly-brain project](https://github.com/eonsystemspbc/fly-brain).

The intended first target is the existing FlyWire v783 leaky integrate-and-fire model, validated against its Brian2 central processing unit (CPU) reference implementation.

## Status

The active goal and mandatory model-handoff protocol are saved in [docs/goal.md](docs/goal.md). This specification supersedes the earlier planning charter.

Startup inspection confirmed Apple silicon and available `uv` tooling. No upstream source has been fetched or pinned, no numerical experiments have run, and no backend implementation has begun. The active session was verified as GPT-6.1 Sol at `xhigh`; the goal requires GPT-5.6 Sol at `xhigh` for routine work. Startup is awaiting that model selection. See [execution startup notes](docs/handoffs/execution-start.md).

## Project context

- [Active goal and model-handoff protocol](docs/goal.md)
- [Execution startup notes](docs/handoffs/execution-start.md)
- [Earlier project charter, superseded](docs/project-charter.md)
- [Working rules](AGENTS.md)

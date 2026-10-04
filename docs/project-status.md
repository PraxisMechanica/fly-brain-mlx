# MLX fly-brain backend

Workspace for an Apple MLX backend for the [Eon Systems fly-brain project](https://github.com/eonsystemspbc/fly-brain).

The intended first target is the existing FlyWire v783 leaky integrate-and-fire model, validated against its Brian2 central processing unit (CPU) reference implementation.

## Status

The active goal and mandatory model-handoff protocol are saved in [goal.md](goal.md). This specification supersedes the earlier planning charter.

Startup inspection confirmed Apple silicon and available `uv` tooling. Reference baseline work is beginning; no numerical experiments or backend implementation have begun. The user controls model changes and has removed the original GPT-5.6 requirement. See [execution startup notes](handoffs/execution-start.md).

## Project context

- [Active goal and model-handoff protocol](goal.md)
- [Execution startup notes](handoffs/execution-start.md)
- [Earlier project charter, superseded](project-charter.md)
- [Working rules](../AGENTS.md)

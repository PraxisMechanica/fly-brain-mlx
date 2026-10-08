from pathlib import Path


def require_retained_output(resolved_output: Path, project: Path | None = None) -> None:
    roots = (Path.cwd(),) if project is None else (Path.cwd(), project)
    for root in roots:
        if resolved_output.is_relative_to((root / 'logs').resolve()):
            raise ValueError('Scientific output cannot be placed under disposable logs')

import os
from collections.abc import Callable
from pathlib import Path
from typing import Annotated

from pydantic import BaseModel, Field

from tools.code_quality.gate import git

CommitHash = Annotated[str, Field(pattern=r'^[0-9a-f]{40}$')]


class Commit(BaseModel):
    sha: CommitHash


class PullRequest(BaseModel):
    base: Commit
    head: Commit


class Event(BaseModel):
    before: CommitHash | None = None
    forced: bool = False
    pull_request: PullRequest | None = None


def select(
    event: Event,
    head: str,
    execute: Callable[[str, str, str], str],
) -> tuple[str, str]:
    head = Commit(sha=head).sha
    if event.pull_request is not None:
        head = event.pull_request.head.sha
        base = execute('merge-base', event.pull_request.base.sha, head)
    elif event.forced or not event.before or set(event.before) == {'0'}:
        base = execute('merge-base', 'origin/main', head)
    else:
        base = event.before
    if base == head:
        base = execute('rev-parse', '--verify', f'{head}^')
    return Commit(sha=base).sha, head


def main() -> None:
    event = Event.model_validate_json(Path(os.environ['GITHUB_EVENT_PATH']).read_text())
    base, head = select(event, os.environ['GITHUB_SHA'], git)
    with Path(os.environ['GITHUB_ENV']).open('a') as output:
        output.write(f'QUALITY_BASE={base}\nQUALITY_HEAD={head}\n')


if __name__ == '__main__':
    main()

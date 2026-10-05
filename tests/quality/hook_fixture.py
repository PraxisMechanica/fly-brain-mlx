import os
import re
import shutil
import sys
from pathlib import Path

from tests.quality.support import PROJECT, git, repository, run

GOOD = 'from fly_brain.simulation.models import VALUE\n'
BAD = 'from fly_brain.simulation.backend import VALUE\n'
SERVICE = 'src/fly_brain/simulation/service.py'


def hook_repository(root: Path, source: str = GOOD) -> tuple[Path, dict[str, str]]:
    repo = repository(root)
    policy = (
        '[tool.importlinter]'
        + (PROJECT / 'pyproject.toml').read_text().split('[tool.importlinter]', 1)[1]
    )
    (repo / 'pyproject.toml').write_text(policy)
    for module in sorted(set(re.findall(r'"(fly_brain(?:\.[a-z_]+)*)"', policy))):
        relative = Path('src', *module.split('.'))
        path = relative.with_suffix('.py')
        if not (PROJECT / path).is_file():
            path = relative / '__init__.py'
        (repo / path).parent.mkdir(parents=True, exist_ok=True)
        (repo / path).write_text('VALUE = 1\n')
        for parent in relative.parents:
            if parent == Path('src') or parent == Path('.'):
                break
            (repo / parent / '__init__.py').touch()
    (repo / SERVICE).write_text(source)
    for name in ('.pre-commit-config.yaml', 'justfile'):
        shutil.copyfile(PROJECT / name, repo / name)
    tools = repo / 'executables'
    tools.mkdir()
    (repo / '.gitignore').write_text('executables/\n')
    just, imports = shutil.which('just'), shutil.which('lint-imports')
    assert just is not None and imports is not None
    (tools / 'just').symlink_to(just)
    executable = tools / 'uv'
    executable.write_text(
        f'#!{sys.executable}\n'
        'import os, subprocess, sys\n'
        "arguments = ' '.join(sys.argv[1:])\n"
        "failure = os.environ.get('FAIL_TOOL')\n"
        'if failure and failure in arguments:\n'
        "    print('controlled tool failure: ' + failure)\n"
        '    sys.exit(23)\n'
        "if 'lint-imports' in arguments:\n"
        f"    sys.exit(subprocess.call([{imports!r}, '--no-cache']))\n"
    )
    executable.chmod(0o755)
    git(repo, 'add', '.')
    git(repo, 'commit', '-qm', 'Create source only hook fixture')
    environment = {
        'PATH': str(tools) + os.pathsep + '/usr/bin:/bin',
        'PYTHONPATH': str(repo / 'src'),
        'PRE_COMMIT_HOME': os.environ.get(
            'PRE_COMMIT_HOME', '/private/tmp/fly-brain-pre-commit-cache'
        ),
        'LC_ALL': 'C',
    }
    cache = Path(environment['PRE_COMMIT_HOME']).resolve()
    assert not cache.is_relative_to(repo.resolve())
    installed = run(
        [
            sys.executable,
            '-m',
            'pre_commit',
            'install',
            '--hook-type',
            'pre-commit',
            '--hook-type',
            'pre-push',
        ],
        repo,
        environment,
    )
    assert installed.returncode == 0, installed.stderr
    assert all(
        (repo / '.git/hooks' / stage).is_file() for stage in ('pre-commit', 'pre-push')
    )
    return repo, environment


def commit_document(repo: Path, environment: dict[str, str]):
    (repo / 'README.md').write_text('Documentation-only source fixture\n')
    git(repo, 'add', 'README.md')
    return run(
        ['git', 'commit', '-m', 'Document source fixture behavior'], repo, environment
    )

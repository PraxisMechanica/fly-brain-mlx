import shutil
import subprocess
import sys
from pathlib import Path


def clean_logs(root: Path) -> None:
    directory = root / 'logs'
    if directory.is_symlink():
        raise ValueError('Refusing to clean a symlinked logs directory')
    if not directory.exists():
        return
    if not directory.is_dir():
        raise ValueError('The logs path must be a directory')
    tracked = subprocess.check_output(['git', 'ls-files', '-z', '--', 'logs'], cwd=root)
    if tracked:
        raise ValueError('Refusing to clean versioned files under logs')
    shutil.rmtree(directory)


def main() -> int:
    try:
        clean_logs(Path.cwd())
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(f'Diagnostic cleanup failed: {error}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())

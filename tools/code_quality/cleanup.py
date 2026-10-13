import subprocess
import sys
from pathlib import Path

from .retention import clean_outputs


def clean_logs(root: Path) -> None:
    clean_outputs(root)


def main() -> int:
    try:
        clean_logs(Path.cwd())
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(f'Output cleanup failed: {error}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())

import os


def isolated_environment() -> dict[str, str]:
    return {
        key: value for key, value in os.environ.items() if not key.startswith('GIT_')
    }

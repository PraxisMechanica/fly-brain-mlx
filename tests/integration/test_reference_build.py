from pathlib import Path

import pytest

from fly_brain.qualification.adapters import reference_build

pytestmark = pytest.mark.integration


@pytest.mark.parametrize('kind', ('framework', 'shared-library', 'executable'))
def test_snapshot_binds_the_actual_python_runtime(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    executable = tmp_path / 'python'
    executable.write_bytes(b'python executable')
    library = tmp_path / 'libpython3.10.dylib'
    library.write_bytes(b'standalone shared runtime')
    framework = tmp_path / 'Python.framework/Versions/3.10/Python'
    framework.parent.mkdir(parents=True)
    framework.write_bytes(b'framework runtime')
    (tmp_path / 'SDKSettings.json').write_text('{}')
    settings = {
        'PYTHONFRAMEWORK': 'Python' if kind == 'framework' else '',
        'PYTHONFRAMEWORKPREFIX': str(tmp_path),
        'VERSION': '3.10',
        'Py_ENABLE_SHARED': int(kind == 'shared-library'),
        'LIBDIR': str(tmp_path),
        'LDLIBRARY': library.name,
    }
    monkeypatch.setattr(reference_build.sysconfig, 'get_config_var', settings.get)
    monkeypatch.setattr(reference_build.sys, 'executable', str(executable))

    def packages() -> dict[str, object]:
        return {}

    monkeypatch.setattr(reference_build, 'installed_packages', packages)

    def command(*arguments: str, directory: Path | None = None) -> str:
        return (
            str(executable)
            if arguments == ('xcrun', '--find', 'clang++')
            else str(tmp_path)
        )

    monkeypatch.setattr(reference_build, 'command', command)
    runtime = {
        'framework': framework,
        'shared-library': library,
        'executable': executable,
    }[kind]
    snapshot = reference_build.snapshot()
    assert snapshot['python_runtime'] == {
        'kind': kind,
        'path': str(runtime),
        'file': reference_build.file_record(runtime),
    }
    runtime.write_bytes(b'changed runtime')
    assert reference_build.snapshot() != snapshot
    runtime.unlink()
    with pytest.raises(FileNotFoundError):
        reference_build.snapshot()

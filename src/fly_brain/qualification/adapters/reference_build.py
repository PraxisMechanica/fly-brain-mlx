import os
import platform
import shlex
import shutil
import subprocess
import sys
import sysconfig
from pathlib import Path

import brian2 as b

from .reference_identity import file_record, installed_packages


def command(*arguments: str, directory: Path | None = None) -> str:
    return subprocess.check_output(
        arguments, cwd=directory, text=True, stderr=subprocess.PIPE, timeout=60
    ).strip()


def snapshot() -> dict[str, object]:
    sdk = Path(command('xcrun', '--show-sdk-path'))
    compiler = Path(command('xcrun', '--find', 'clang++'))
    framework = (
        Path(str(sysconfig.get_config_var('PYTHONFRAMEWORKPREFIX')))
        / (str(sysconfig.get_config_var('PYTHONFRAMEWORK')) + '.framework')
        / 'Versions'
        / str(sysconfig.get_config_var('VERSION'))
        / str(sysconfig.get_config_var('PYTHONFRAMEWORK'))
    )
    return {
        'preferences': b.prefs.as_file,
        'packages': installed_packages(),
        'python': sys.version,
        'python_executable': file_record(Path(sys.executable)),
        'python_framework': file_record(framework),
        'os_build': command('sw_vers', '-buildVersion'),
        'platform': platform.platform(),
        'processor': command('sysctl', '-n', 'machdep.cpu.brand_string'),
        'compiler': file_record(compiler),
        'compiler_version': command(str(compiler), '--version'),
        'sdk': str(sdk),
        'sdk_settings': file_record(sdk / 'SDKSettings.json'),
        'environment': {
            name: value
            for name, value in os.environ.items()
            if name
            in (
                'CC',
                'CXX',
                'CPP',
                'LD',
                'CFLAGS',
                'CXXFLAGS',
                'CPPFLAGS',
                'LDFLAGS',
                'CPATH',
                'CPLUS_INCLUDE_PATH',
                'LIBRARY_PATH',
                'SDKROOT',
                'DEVELOPER_DIR',
                'MACOSX_DEPLOYMENT_TARGET',
                'PATH',
                'LANG',
                'MAKEFLAGS',
                'GNUMAKEFLAGS',
                'MFLAGS',
            )
            or name.startswith(('DYLD_', 'LC_'))
        },
        'source_inventory': {
            name: file_record(Path(__file__).with_name(name))
            for name in (
                'brian_reference.py',
                'brian_jobs.py',
                'brian_observer.py',
                'observer_stream.py',
                'observer_tape.py',
            )
        },
    }


def consumed_dependencies(directory: Path, started_ns: int) -> dict[str, object]:
    makefile = (directory / 'makefile').read_text()
    script = makefile + (
        '\n$(info FBREF-COMPILE=$(CXX) $(CXXFLAGS))\n'
        '$(info FBREF-LINK=$(CXX) $(LFLAGS))\n'
        '$(info FBREF-SOURCES=$(SRCS))\n'
    )
    expanded = subprocess.run(
        ['make', '-n', '-f', '-', 'main'],
        input=script,
        cwd=directory,
        text=True,
        check=True,
        capture_output=True,
        timeout=60,
    ).stdout
    settings = {
        name: next(
            line.split('=', 1)[1]
            for line in expanded.splitlines()
            if line.startswith('FBREF-' + name + '=')
        )
        for name in ('COMPILE', 'LINK', 'SOURCES')
    }
    compiler = shlex.split(settings['COMPILE'])
    resolved = shutil.which(compiler[0])
    if resolved is None:
        raise ValueError('Cannot bind the actual reference compiler')
    compiler_path = Path(resolved).resolve()
    sources = shlex.split(settings['SOURCES'])
    arguments = [value for value in compiler if value != '-c']
    dependencies = command(*arguments, '-M', *sources, directory=directory)
    tokens = shlex.split(dependencies.replace('\\\n', ' '))
    external = sorted(
        {(directory / token).resolve() for token in tokens if not token.endswith(':')}
        - {path.resolve() for path in directory.rglob('*') if path.is_file()}
    )
    if any(path.stat().st_mtime_ns > started_ns for path in external):
        raise ValueError('A consumed reference dependency changed during build')
    linked = command('otool', '-L', str(directory / 'main'))
    runtime = {
        path: file_record(Path(path))
        for line in linked.splitlines()[1:]
        if (path := line.strip().split(' ', 1)[0]) and Path(path).is_file()
    }
    if any(line.strip().startswith('@') for line in linked.splitlines()[1:]):
        raise ValueError('Cannot bind an unresolved reference runtime library')
    return {
        'resolved_commands': settings,
        'actual_compiler': file_record(compiler_path),
        'actual_compiler_version': command(str(compiler_path), '--version'),
        'consumed_headers': {str(path): file_record(path) for path in external},
        'linked_runtime': linked.splitlines()[1:],
        'runtime_files': runtime,
        'system_runtime_identity': 'Sealed operating-system build; shared-cache libraries',
    }

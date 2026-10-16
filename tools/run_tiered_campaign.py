"""Profile and run independent CPU references beside one MLX GPU worker."""

import argparse
import importlib.metadata
import json
import math
import os
import shutil
import signal
import subprocess
import sys
from collections.abc import Callable
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from time import perf_counter, sleep
from typing import IO

from pydantic import BaseModel, ConfigDict

from fly_brain.infrastructure.output_paths import require_retained_output
from fly_brain.simulation.models import ExperimentName

from .campaign_resources import (
    GIB,
    Allocation,
    Hardware,
    Sample,
    allocate,
    available_memory,
    candidates,
    detect,
    makespan,
    select,
)
from .tiered_trial import (
    Engine,
    Job,
    digest,
    package_versions,
    producer_sources,
    sources,
)

EXPERIMENTS: tuple[ExperimentName, ...] = (
    'sugar',
    'p9',
    'sugar-silenced',
    'two-class',
    'silent',
)
THREADS = {
    'OMP_NUM_THREADS': '1',
    'OPENBLAS_NUM_THREADS': '1',
    'MKL_NUM_THREADS': '1',
    'VECLIB_MAXIMUM_THREADS': '1',
    'NUMEXPR_NUM_THREADS': '1',
    'MLX_ENABLE_TF32': '0',
}


class TrialEvidence(BaseModel):
    model_config = ConfigDict(strict=True, extra='allow')
    completed: bool
    job: Job
    source_sha256: dict[str, str]
    artifact_sha256: dict[str, str]
    reference_executable_sha256: str | None = None
    seed: int
    memory_envelope_bytes: int
    elapsed_s: float
    python: str
    python_executable_sha256: str
    versions: dict[str, str]
    effective_thread_environment: dict[str, str]
    execution_identity: dict[str, str]
    arrow_cpu_threads: int
    arrow_io_threads: int
    device: str | None = None
    MLX_ENABLE_TF32: str | None = None
    compilation: str | None = None


class Completed(BaseModel):
    model_config = ConfigDict(strict=True, extra='forbid')
    job: Job
    directory: Path
    trial_sha256: str
    wall_s: float
    sampled_tree_peak_bytes: int
    memory_envelope_bytes: int
    retained_bytes: int = 0
    started_s: float = 0
    finished_s: float = 0


class Profile(BaseModel):
    model_config = ConfigDict(strict=True, extra='forbid')
    hardware: Hardware
    allocation: Allocation
    isolated: list[Completed]
    coupled: list[Sample]
    source_sha256: dict[str, str]
    versions: dict[str, str]
    threads: dict[str, str]
    scope: str
    execution_identity: dict[Engine, dict[str, str]]


class Campaign(BaseModel):
    model_config = ConfigDict(strict=True, extra='forbid')
    jobs: tuple[Job, ...]
    reused: list[Completed]
    profile_path: Path
    profile_sha256: str
    estimated_hours: float
    estimated_bytes: int
    source_sha256: dict[str, str]
    silent_trials: int = 30


def jobs(silent_trials: int = 30) -> tuple[Job, ...]:
    if type(silent_trials) is not int or not 1 <= silent_trials <= 30:
        raise ValueError('Silent cohort size must be an integer from 1 to 30')
    cohorts: tuple[tuple[Engine, int], ...] = (
        ('brian', 1000),
        ('mlx', 0),
        ('mlx', 2000),
    )
    return tuple(
        Job(engine, experiment, trial)
        for experiment in EXPERIMENTS
        for engine, start in cohorts
        for trial in range(
            start, start + (silent_trials if experiment == 'silent' else 30)
        )
    )


def write(path: Path, value: object) -> None:
    if isinstance(value, BaseModel):
        value = value.model_dump(mode='json')
    with path.open('x') as destination:
        destination.write(json.dumps(value, indent=2, allow_nan=False) + '\n')


def environment() -> dict[str, str]:
    result = dict(os.environ)
    for name in ('MAKEFLAGS', 'GNUMAKEFLAGS', 'MFLAGS'):
        result.pop(name, None)
    result.update(THREADS)
    return result


def versions() -> dict[str, str]:
    return {
        name: importlib.metadata.version(name)
        for name in ('numpy', 'brian2', 'mlx', 'mlx-metal', 'pyarrow')
    }


def swap_bytes() -> int:
    import re

    text = subprocess.check_output(('sysctl', '-n', 'vm.swapusage'), text=True)
    match = re.search(r'used = ([0-9.]+)([MG])', text)
    if match is None:
        raise ValueError('Cannot read system swap usage')
    return int(float(match[1]) * (1024**2 if match[2] == 'M' else GIB))


def tree_memory(pids: tuple[int, ...]) -> dict[int, int]:
    if not pids:
        return {}
    output = subprocess.check_output(('ps', '-axo', 'pid=,ppid=,rss='), text=True)
    processes = [tuple(map(int, line.split())) for line in output.splitlines()]
    measured: dict[int, int] = {}
    for root in pids:
        descendants = {root}
        while True:
            added = {pid for pid, parent, _ in processes if parent in descendants}
            if added <= descendants:
                break
            descendants |= added
        measured[root] = sum(
            rss * 1024 for pid, _, rss in processes if pid in descendants
        )
    return measured


def signal_owned_group(group: int, signum: int) -> None:
    def live() -> bool:
        rows = subprocess.check_output(('ps', '-axo', 'pgid=,state='), text=True)
        return any(
            int(parts[0]) == group and not parts[1].startswith('Z')
            for line in rows.splitlines()
            if len(parts := line.split()) == 2
        )

    if not live():
        return
    try:
        os.killpg(group, signum)
    except ProcessLookupError:
        return
    except PermissionError:
        if live():
            raise


def verify(
    directory: Path,
    job: Job,
    identity: dict[str, str],
    expected_execution: dict[str, str] | None = None,
) -> TrialEvidence:
    report = TrialEvidence.model_validate_json((directory / 'trial.json').read_text())
    if (
        report.completed is not True
        or report.job != job
        or producer_sources(report.source_sha256) != producer_sources(identity)
        or report.seed != 20261004
        or not {'stimulus.json', 'stimulus.npz', 'spikes.npz'}
        <= report.artifact_sha256.keys()
    ):
        raise ValueError('Completed trial identity or evidence is incompatible')
    if (
        report.python != sys.version
        or report.python_executable_sha256 != digest(Path(sys.executable).resolve())
        or report.versions != package_versions(job.engine)
        or report.effective_thread_environment != THREADS
        or report.arrow_cpu_threads != 1
        or report.arrow_io_threads != 1
    ):
        raise ValueError(
            'Completed worker environment differs from the pinned execution'
        )
    if (
        expected_execution is not None
        and report.execution_identity != expected_execution
    ):
        raise ValueError('Worker runtime/toolchain differs from its measured profile')
    if job.engine == 'mlx' and (
        report.device != detect().gpu_name
        or report.MLX_ENABLE_TF32 != '0'
        or report.compilation != 'disabled'
    ):
        raise ValueError('GPU device/precision differs from the qualified mode')
    for name, expected in report.artifact_sha256.items():
        path = directory / name
        if (
            Path(name).is_absolute()
            or '..' in Path(name).parts
            or digest(path) != expected
        ):
            raise ValueError('Completed trial artifact changed: ' + name)
    if job.engine == 'brian':
        if (
            digest(directory / 'reference-build/main')
            != report.reference_executable_sha256
        ):
            raise ValueError('Retained reference executable changed')
    return report


@dataclass
class Active:
    job: Job
    directory: Path
    process: subprocess.Popen[bytes]
    log: IO[bytes]
    started: float
    peak_tree_bytes: int = 0


def worker_command(project: Path, job: Job, output: Path) -> list[str]:
    return [
        sys.executable,
        '-m',
        'tools.tiered_trial',
        '--project',
        str(project),
        '--output',
        str(output),
        '--job',
        json.dumps(asdict(job)),
    ]


def execute(
    project: Path,
    output: Path,
    selected: tuple[Job, ...],
    allocation: Allocation,
    *,
    deadline: float,
    command: Callable[[Path, Job, Path], list[str]] = worker_command,
    memory: Callable[[], int] = available_memory,
    swap: Callable[[], int] = swap_bytes,
    expected_execution: dict[Engine, dict[str, str]] | None = None,
) -> list[Completed]:
    require_retained_output(output.resolve(), project)
    if len({job.name for job in selected}) != len(selected):
        raise ValueError('A wave requires unique trial identities')
    output.mkdir(parents=True, exist_ok=False)
    (output / 'commands').mkdir()
    identity = sources(project)
    write(
        output / 'wave.json',
        {
            'jobs': [asdict(job) for job in selected],
            'allocation': asdict(allocation),
            'source_sha256': identity,
        },
    )
    pending = list(selected)
    active: list[Active] = []
    completed: list[Completed] = []
    initial_swap = swap()
    last_sample = 0.0
    started = perf_counter()
    failure: str | None = None
    try:
        with (output / 'memory-samples.jsonl').open('x') as samples:
            while pending or active:
                if perf_counter() >= deadline:
                    raise TimeoutError('Coordinator deadline reached')
                for worker in tuple(active):
                    code = worker.process.poll()
                    if code is None:
                        continue
                    worker.log.close()
                    if code:
                        raise RuntimeError(
                            f'{worker.job.name} exited {code}; see commands/'
                        )
                    finished = perf_counter()
                    report = verify(
                        worker.directory,
                        worker.job,
                        identity,
                        expected_execution[worker.job.engine]
                        if expected_execution is not None
                        else None,
                    )
                    completed.append(
                        Completed(
                            job=worker.job,
                            directory=worker.directory,
                            trial_sha256=digest(worker.directory / 'trial.json'),
                            wall_s=finished - worker.started,
                            sampled_tree_peak_bytes=worker.peak_tree_bytes,
                            memory_envelope_bytes=report.memory_envelope_bytes,
                            retained_bytes=sum(
                                path.stat().st_size
                                for path in worker.directory.rglob('*')
                                if path.is_file()
                            ),
                            started_s=worker.started - started,
                            finished_s=finished - started,
                        )
                    )
                    write(output / (worker.job.name + '-completed.json'), completed[-1])
                    signal_owned_group(worker.process.pid, signal.SIGTERM)
                    signal_owned_group(worker.process.pid, signal.SIGKILL)
                    active.remove(worker)
                if perf_counter() - last_sample >= 1:
                    peaks = tree_memory(tuple(worker.process.pid for worker in active))
                    free = memory()
                    current_swap = swap()
                    for worker in active:
                        worker.peak_tree_bytes = max(
                            worker.peak_tree_bytes, peaks[worker.process.pid]
                        )
                    samples.write(
                        json.dumps(
                            {
                                'elapsed_s': perf_counter() - started,
                                'available_bytes': free,
                                'swap_bytes': current_swap,
                                'rss_bytes_by_pid': peaks,
                            }
                        )
                        + '\n'
                    )
                    samples.flush()
                    last_sample = perf_counter()
                    if current_swap > initial_swap + 16 * 1024**2:
                        raise MemoryError(
                            'Swap grew during the pilot/campaign; lower concurrency'
                        )
                for job in tuple(pending):
                    cpu = sum(worker.job.engine == 'brian' for worker in active)
                    gpu = sum(worker.job.engine == 'mlx' for worker in active)
                    if job.engine == 'brian' and cpu >= allocation.cpu_workers:
                        continue
                    if job.engine == 'mlx' and gpu >= allocation.gpu_workers:
                        continue
                    required = (
                        allocation.cpu_worker_bytes
                        if job.engine == 'brian'
                        else allocation.gpu_worker_bytes
                    )
                    reserved = (
                        cpu * allocation.cpu_worker_bytes
                        + gpu * allocation.gpu_worker_bytes
                    )
                    if (
                        reserved + required > allocation.memory_budget_bytes
                        or memory() < allocation.memory_headroom_bytes + required
                    ):
                        continue
                    directory = output / 'jobs' / job.name
                    log = (output / 'commands' / (job.name + '.log')).open('xb')
                    try:
                        process = subprocess.Popen(
                            command(project, job, directory),
                            cwd=project,
                            env=environment(),
                            stdout=log,
                            stderr=subprocess.STDOUT,
                            start_new_session=True,
                        )
                    except BaseException:
                        log.close()
                        raise
                    active.append(Active(job, directory, process, log, perf_counter()))
                    pending.remove(job)
                if pending and not active:
                    raise MemoryError('Available memory cannot admit a pending worker')
                if active:
                    sleep(0.1)
        if identity != sources(project):
            raise ValueError('Sources changed during the wave')
    except BaseException as error:
        failure = f'{type(error).__name__}: {error}'
        raise
    finally:
        for worker in active:
            signal_owned_group(worker.process.pid, signal.SIGTERM)
        for worker in active:
            try:
                worker.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                signal_owned_group(worker.process.pid, signal.SIGKILL)
                worker.process.wait(timeout=5)
            worker.log.close()
            signal_owned_group(worker.process.pid, signal.SIGKILL)
        write(
            output / 'result.json',
            {
                'completed': [row.model_dump(mode='json') for row in completed],
                'failure': failure,
                'elapsed_s': perf_counter() - started,
                'pending': [asdict(job) for job in pending],
                'interrupted': [asdict(worker.job) for worker in active],
            },
        )
    return completed


def pilot(project: Path, output: Path, *, max_hours: float, os_cores: int) -> Profile:
    require_retained_output(output.resolve(), project)
    hardware = detect()
    identity = sources(project)
    software = versions()
    if os_cores < 1 or hardware.cpu_cores < os_cores + 3:
        raise ValueError('Reserve OS/host capacity before starting pilot workers')
    output.mkdir(parents=True, exist_ok=False)
    deadline = perf_counter() + max_hours * 3600
    headroom = max(8 * GIB, math.ceil(hardware.memory_bytes * 0.1))
    initial = Allocation(
        1, hardware.memory_bytes - headroom, headroom, 8 * GIB, 8 * GIB, os_cores + 1
    )
    isolated: list[Completed] = []
    execution_identity: dict[Engine, dict[str, str]] = {}
    for experiment in EXPERIMENTS:
        for engine in ('brian', 'mlx'):
            if sources(project) != identity:
                raise ValueError('Scientific sources changed between pilot waves')
            measured = execute(
                project,
                output / f'isolated-{engine}-{experiment}',
                (Job(engine, experiment, 0),),
                initial,
                deadline=deadline,
            )
            for row in measured:
                report = verify(
                    row.directory,
                    row.job,
                    identity,
                    execution_identity.get(row.job.engine),
                )
                execution_identity[row.job.engine] = report.execution_identity
            isolated.extend(measured)
    cpu_peak = max(
        max(row.memory_envelope_bytes, row.sampled_tree_peak_bytes)
        for row in isolated
        if row.job.engine == 'brian'
    )
    gpu_peak = max(
        max(row.memory_envelope_bytes, row.sampled_tree_peak_bytes)
        for row in isolated
        if row.job.engine == 'mlx'
    )
    capacity = allocate(hardware, cpu_peak, gpu_peak, os_cores=os_cores)
    baseline_gpu = next(
        row.wall_s
        for row in isolated
        if row.job.engine == 'mlx' and row.job.experiment == 'sugar'
    )
    samples: list[Sample] = []
    for count in candidates(capacity.cpu_workers):
        if count > capacity.cpu_workers:
            break
        if sources(project) != identity:
            raise ValueError('Scientific sources changed between pilot waves')
        wave = tuple(Job('brian', 'sugar', trial) for trial in range(count)) + (
            Job('mlx', 'sugar', 0),
        )
        records = execute(
            project,
            output / f'coupled-{count}',
            wave,
            replace(capacity, cpu_workers=count),
            deadline=deadline,
            expected_execution=execution_identity,
        )
        sample = Sample(
            count,
            max(row.finished_s for row in records if row.job.engine == 'brian')
            - min(row.started_s for row in records if row.job.engine == 'brian'),
            next(row.wall_s for row in records if row.job.engine == 'mlx'),
        )
        cpu_peak = max(
            cpu_peak,
            *(
                max(row.memory_envelope_bytes, row.sampled_tree_peak_bytes)
                for row in records
                if row.job.engine == 'brian'
            ),
        )
        gpu_peak = max(
            gpu_peak,
            *(
                max(row.memory_envelope_bytes, row.sampled_tree_peak_bytes)
                for row in records
                if row.job.engine == 'mlx'
            ),
        )
        capacity = allocate(hardware, cpu_peak, gpu_peak, os_cores=os_cores)
        if sample.gpu_s > baseline_gpu * 1.1:
            if not samples:
                raise ValueError(
                    'Even one reference worker materially slows MLX; review sequential scheduling before campaign adoption'
                )
            break
        if (
            samples
            and sample.campaign_s(150, 300) >= samples[-1].campaign_s(150, 300) * 0.97
        ):
            break
        samples.append(sample)
    samples = [
        sample for sample in samples if sample.cpu_workers <= capacity.cpu_workers
    ]
    chosen = select(tuple(samples), cpu_jobs=150, gpu_jobs=300)
    if sources(project) != identity:
        raise ValueError('Scientific sources changed during the pilot')
    report = Profile(
        hardware=hardware,
        allocation=replace(capacity, cpu_workers=chosen),
        isolated=isolated,
        coupled=samples,
        source_sha256=identity,
        versions=software,
        threads=THREADS,
        scope='Same-machine performance calibration; scientific qualification and long-campaign approval remain separate.',
        execution_identity=execution_identity,
    )
    write(output / 'profile.json', report)
    return report


def campaign(
    project: Path,
    output: Path,
    profile_path: Path,
    *,
    max_hours: float,
    resume: Path | None,
    plan_only: bool = False,
    silent_trials: int = 30,
) -> dict[str, object]:
    profile = Profile.model_validate_json(profile_path.read_text())
    identity = sources(project)
    if (
        profile.hardware != detect()
        or profile.source_sha256 != identity
        or profile.versions != versions()
        or profile.threads != THREADS
    ):
        raise ValueError(
            'Profile must match this machine, sources and installed versions'
        )
    allocation = profile.allocation
    if (
        allocation.cpu_workers * 2 + allocation.reserved_cpu_cores
        > profile.hardware.cpu_cores
        or allocation.reserved_cpu_cores < 3
        or allocation.memory_budget_bytes + allocation.memory_headroom_bytes
        > profile.hardware.memory_bytes
        or allocation.cpu_workers * allocation.cpu_worker_bytes
        + allocation.gpu_worker_bytes
        > allocation.memory_budget_bytes
    ):
        raise ValueError('Profile allocation exceeds reserved hardware capacity')
    selected = jobs(silent_trials)
    reused: list[Completed] = []
    for row in profile.isolated:
        if row.job in selected and row.job not in {item.job for item in reused}:
            if digest(row.directory / 'trial.json') != row.trial_sha256:
                raise ValueError('Pilot evidence receipt changed')
            verify(
                row.directory,
                row.job,
                identity,
                profile.execution_identity[row.job.engine],
            )
            reused.append(row)
    if resume is not None:
        previous = Campaign.model_validate_json((resume / 'campaign.json').read_text())
        if previous.jobs != selected or producer_sources(
            previous.source_sha256
        ) != producer_sources(identity):
            raise ValueError('Resume profile changed')
        originals = previous.reused + [
            Completed.model_validate_json(path.read_text())
            for path in sorted(resume.rglob('*-completed.json'))
        ]
        indexed = {row.job for row in originals}
        for job in selected:
            directory = resume / 'wave/jobs' / job.name
            if job not in indexed and (directory / 'trial.json').is_file():
                report = verify(directory, job, identity)
                originals.append(
                    Completed(
                        job=job,
                        directory=directory,
                        trial_sha256=digest(directory / 'trial.json'),
                        wall_s=report.elapsed_s,
                        sampled_tree_peak_bytes=0,
                        memory_envelope_bytes=report.memory_envelope_bytes,
                        retained_bytes=sum(
                            path.stat().st_size
                            for path in directory.rglob('*')
                            if path.is_file()
                        ),
                    )
                )
        for row in originals:
            job = row.job
            if job not in selected:
                raise ValueError('Resume contains an unplanned trial')
            directory = row.directory
            if digest(directory / 'trial.json') != row.trial_sha256:
                raise ValueError('Completed trial receipt changed')
            verify(directory, job, identity, profile.execution_identity[job.engine])
            if job not in {item.job for item in reused}:
                reused.append(row)
    complete = {row.job for row in reused}
    if len(complete) != len(reused):
        raise ValueError('Resume contains duplicate completed trials')
    pending = tuple(job for job in selected if job not in complete)
    timing = {
        (row.job.engine, row.job.experiment): row.wall_s for row in profile.isolated
    }
    sample = next(
        sample
        for sample in profile.coupled
        if sample.cpu_workers == allocation.cpu_workers
    )
    cpu_slowdown = max(1, sample.cpu_wave_s / timing[('brian', 'sugar')])
    cpu_s = makespan(
        tuple(
            timing[(job.engine, job.experiment)] * cpu_slowdown
            for job in pending
            if job.engine == 'brian'
        ),
        allocation.cpu_workers,
    )
    gpu_s = sum(
        timing[(job.engine, job.experiment)] for job in pending if job.engine == 'mlx'
    )
    slowdown = sample.gpu_s / timing[('mlx', 'sugar')]
    estimated_s = max(cpu_s, gpu_s * max(1, slowdown)) * 1.25
    storage = {
        (row.job.engine, row.job.experiment): row.retained_bytes
        for row in profile.isolated
    }
    estimated_bytes = math.ceil(
        sum(storage[(job.engine, job.experiment)] for job in pending) * 1.25
    )
    if not plan_only and estimated_s > max_hours * 3600:
        raise ValueError(
            f'Priced campaign needs approximately {estimated_s / 3600:.2f} hours including25% allowance; explicit approval and a matching --max-hours limit are required'
        )
    require_retained_output(output.resolve(), project)
    if not plan_only:
        existing = output.parent
        while not existing.exists():
            existing = existing.parent
        if shutil.disk_usage(existing).free < estimated_bytes + 8 * GIB:
            raise ValueError(
                'Insufficient free disk for measured retained evidence plus headroom'
            )
    output.mkdir(parents=True, exist_ok=False)
    write(
        output / 'campaign.json',
        Campaign(
            jobs=selected,
            reused=reused,
            profile_path=profile_path.resolve(),
            profile_sha256=digest(profile_path),
            estimated_hours=estimated_s / 3600,
            estimated_bytes=estimated_bytes,
            source_sha256=identity,
            silent_trials=silent_trials,
        ),
    )
    if plan_only:
        return {
            'estimated_hours': estimated_s / 3600,
            'estimated_bytes': estimated_bytes,
            'remaining_jobs': len(pending),
            'allocation': asdict(allocation),
            'plan_only': True,
        }
    completed = execute(
        project,
        output / 'wave',
        pending,
        allocation,
        deadline=perf_counter() + max_hours * 3600,
        expected_execution=profile.execution_identity,
    )
    result: dict[str, object] = {
        'execution_complete': len(reused) + len(completed) == len(selected),
        'reused': [row.model_dump(mode='json') for row in reused],
        'completed': [row.model_dump(mode='json') for row in completed],
        'scope': 'Execution complete does not mean statistical or scientific acceptance.',
    }
    write(output / 'result.json', result)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('pilot', 'plan', 'run'))
    parser.add_argument(
        '--project', type=Path, default=Path(__file__).resolve().parents[1]
    )
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--profile', type=Path)
    parser.add_argument('--resume-from', type=Path)
    parser.add_argument('--max-hours', type=float, default=2)
    parser.add_argument('--os-cores', type=int, default=2)
    parser.add_argument(
        '--silent-trials',
        type=int,
        choices=range(1, 31),
        default=30,
        help='Trials per silent cohort; active cohorts always retain 30 trials.',
    )
    args = parser.parse_args()
    if not math.isfinite(args.max_hours) or args.max_hours <= 0:
        parser.error('--max-hours must be positive and finite')
    if args.mode == 'pilot':
        if args.resume_from is not None:
            parser.error(
                'pilot --resume-from is unsupported; preserve the prior pilot and diagnose before a fresh attempt'
            )
        pilot(
            args.project.resolve(),
            args.output.resolve(),
            max_hours=args.max_hours,
            os_cores=args.os_cores,
        )
    elif args.profile is None:
        parser.error('run requires a same-machine --profile')
    else:
        print(
            json.dumps(
                campaign(
                    args.project.resolve(),
                    args.output.resolve(),
                    args.profile.resolve(),
                    max_hours=args.max_hours,
                    resume=args.resume_from,
                    plan_only=args.mode == 'plan',
                    silent_trials=args.silent_trials,
                ),
                indent=2,
            )
        )

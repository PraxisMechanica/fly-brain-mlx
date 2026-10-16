import json
import os
import signal
import subprocess
import sys
from collections.abc import Callable
from contextlib import suppress
from dataclasses import asdict
from pathlib import Path
from time import perf_counter

import pytest

from tools import run_tiered_campaign as runner
from tools.campaign_resources import GIB, Allocation, Hardware, Sample
from tools.tiered_trial import Engine, Job, sources

pytestmark = pytest.mark.integration

WORKER = """
import hashlib, json, os, subprocess, sys, time
from pathlib import Path
job, target, identity, failure, delay = sys.argv[1:]
job, identity = json.loads(job), json.loads(identity)
output = Path(target)
output.mkdir(parents=True)
began = time.monotonic()
(output / 'pid').write_text(str(os.getpid()))
time.sleep(float(delay))
if str(job['trial']) == failure:
    child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)'])
    (output / 'child-pid').write_text(str(child.pid))
    (output / 'diagnostic').write_text('intentional failure')
    sys.exit(7)
files = ['stimulus.json', 'stimulus.npz', 'spikes.npz']
if job['engine'] == 'brian':
    (output / 'reference-build').mkdir()
    files.append('reference-build/main')
for name in files:
    (output / name).write_bytes(name.encode())
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
report = dict(completed=True, job=job, source_sha256=identity, seed=20261004,
              memory_envelope_bytes=1024, elapsed_s=time.monotonic()-began,
              python=sys.version, python_executable_sha256=sha(Path(sys.executable).resolve()),
              versions={'runtime':'test'}, execution_identity={'runtime':'test'},
              effective_thread_environment={name:os.environ.get(name) for name in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS','MLX_ENABLE_TF32')},
              arrow_cpu_threads=1, arrow_io_threads=1,
              artifact_sha256={name: sha(output / name) for name in files})
if job['engine'] == 'mlx':
    report.update(device='test', MLX_ENABLE_TF32='0', compilation='disabled')
if job['engine'] == 'brian':
    report['reference_executable_sha256'] = sha(output / 'reference-build/main')
(output / 'interval.json').write_text(json.dumps([began, time.monotonic()]))
(output / 'trial.json').write_text(json.dumps(report))
"""


@pytest.fixture(autouse=True)
def controlled_runtime(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        runner, 'detect', lambda: Hardware('test', 8, 32 * GIB, 'test', 1)
    )

    def packages(_: Engine) -> dict[str, str]:
        return {'runtime': 'test'}

    monkeypatch.setattr(runner, 'package_versions', packages)
    monkeypatch.setattr(runner, 'versions', lambda: {'runtime': 'test'})


def setup_worker(
    tmp_path: Path,
) -> tuple[Path, Callable[[Path, Job, Path], list[str]], list[Job], set[int]]:
    project = Path(__file__).resolve().parents[2]
    script = tmp_path / 'worker.py'
    script.write_text(WORKER)
    launched: list[Job] = []
    failures: set[int] = set()

    def command(project: Path, job: Job, output: Path) -> list[str]:
        launched.append(job)
        return [
            sys.executable,
            str(script),
            json.dumps(asdict(job)),
            str(output),
            json.dumps(sources(project)),
            str(job.trial) if job.trial in failures else 'none',
            '0.25',
        ]

    return project, command, launched, failures


def allocation(cpu: int = 2) -> Allocation:
    return Allocation(cpu, 16 * GIB, 8 * GIB, GIB, GIB, 3)


def test_real_child_processes_overlap_engines_without_oversubscribing(
    tmp_path: Path,
) -> None:
    project, command, _, _ = setup_worker(tmp_path)
    jobs = tuple(Job('brian', 'sugar', trial) for trial in range(5)) + tuple(
        Job('mlx', 'sugar', trial) for trial in range(3)
    )
    completed = runner.execute(
        project,
        tmp_path / 'wave',
        jobs,
        allocation(),
        deadline=perf_counter() + 20,
        command=command,
        memory=lambda: 128 * GIB,
        swap=lambda: 0,
    )
    intervals = [
        (row.job.engine, *json.loads((row.directory / 'interval.json').read_text()))
        for row in completed
    ]
    overlaps = False
    for _, begin, _ in intervals:
        active = [engine for engine, start, end in intervals if start <= begin < end]
        assert active.count('brian') <= 2
        assert active.count('mlx') <= 1
        overlaps |= 'brian' in active and 'mlx' in active
    assert overlaps and len(completed) == 8


def test_failed_worker_stops_new_admissions_and_keeps_diagnostics(
    tmp_path: Path,
) -> None:
    project, command, launched, failures = setup_worker(tmp_path)
    failures.add(0)
    with pytest.raises(RuntimeError, match='exited 7'):
        runner.execute(
            project,
            tmp_path / 'wave',
            tuple(Job('brian', 'sugar', i) for i in range(3)),
            allocation(1),
            deadline=perf_counter() + 20,
            command=command,
            memory=lambda: 128 * GIB,
            swap=lambda: 0,
        )
    assert [job.trial for job in launched] == [0]
    assert (
        tmp_path / 'wave/jobs/brian-sugar-10000-0/diagnostic'
    ).read_text() == 'intentional failure'
    assert (tmp_path / 'wave/result.json').is_file()
    child = int((tmp_path / 'wave/jobs/brian-sugar-10000-0/child-pid').read_text())
    try:
        state = subprocess.run(
            ['ps', '-p', str(child), '-o', 'state='],
            capture_output=True,
            text=True,
            check=False,
        )
        assert state.returncode != 0 or state.stdout.strip().startswith('Z')
    finally:
        with suppress(ProcessLookupError):
            os.kill(child, signal.SIGTERM)


def test_deadline_terminates_only_coordinator_owned_processes(tmp_path: Path) -> None:
    project, command, _, _ = setup_worker(tmp_path)
    unrelated = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(20)'])
    try:
        with pytest.raises(TimeoutError):
            runner.execute(
                project,
                tmp_path / 'wave',
                (Job('mlx', 'sugar', 0),),
                allocation(),
                deadline=perf_counter() + 0.1,
                command=command,
                memory=lambda: 128 * GIB,
                swap=lambda: 0,
            )
        assert unrelated.poll() is None
        result = json.loads((tmp_path / 'wave/result.json').read_text())
        assert result['failure'].startswith('TimeoutError')
    finally:
        unrelated.terminate()
        unrelated.wait(timeout=5)


def test_chained_resume_never_reruns_or_overwrites_completed_trials(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project, command, launched, failures = setup_worker(tmp_path)
    hardware = Hardware('test', 8, 32 * GIB, 'test', 1)
    selected = tuple(Job('brian', 'sugar', i) for i in range(3))
    monkeypatch.setattr(runner, 'jobs', lambda: selected)
    monkeypatch.setattr(runner, 'detect', lambda: hardware)
    monkeypatch.setattr(runner, 'versions', lambda: {'runtime': 'test'})
    execute = runner.execute

    def controlled(
        project: Path,
        output: Path,
        selected: tuple[Job, ...],
        allocation: Allocation,
        *,
        deadline: float,
        expected_execution: dict[Engine, dict[str, str]] | None = None,
    ) -> list[runner.Completed]:
        return execute(
            project,
            output,
            selected,
            allocation,
            deadline=deadline,
            command=command,
            memory=lambda: 128 * GIB,
            swap=lambda: 0,
            expected_execution=expected_execution,
        )

    monkeypatch.setattr(runner, 'execute', controlled)
    engines: tuple[Engine, ...] = ('brian', 'mlx')
    isolated = [
        runner.Completed(
            job=Job(engine, experiment, 9999),
            directory=tmp_path,
            trial_sha256='unused',
            wall_s=0.1,
            sampled_tree_peak_bytes=1024,
            memory_envelope_bytes=1024,
        )
        for experiment in runner.EXPERIMENTS
        for engine in engines
    ]
    profile = runner.Profile(
        hardware=hardware,
        allocation=allocation(1),
        isolated=isolated,
        coupled=[Sample(1, 0.1, 0.1)],
        source_sha256=sources(project),
        versions={'runtime': 'test'},
        threads=runner.THREADS,
        scope='control test',
        execution_identity={'brian': {'runtime': 'test'}, 'mlx': {'runtime': 'test'}},
    )
    path = tmp_path / 'profile.json'
    runner.write(path, profile)
    failures.add(1)
    first, second, third = (tmp_path / name for name in ('first', 'second', 'third'))
    with pytest.raises(RuntimeError):
        runner.campaign(project, first, path, max_hours=0.01, resume=None)
    original = (first / 'wave/jobs/brian-sugar-10000-0/trial.json').read_bytes()
    (first / 'wave/brian-sugar-10000-0-completed.json').unlink()
    failures.clear()
    failures.add(2)
    with pytest.raises(RuntimeError):
        runner.campaign(project, second, path, max_hours=0.01, resume=first)
    failures.clear()
    result = runner.campaign(project, third, path, max_hours=0.01, resume=second)
    assert result['execution_complete'] is True
    assert [job.trial for job in launched] == [0, 1, 1, 2, 2]
    assert (first / 'wave/jobs/brian-sugar-10000-0/trial.json').read_bytes() == original
    (first / 'wave/jobs/brian-sugar-10000-0/spikes.npz').write_bytes(b'changed')
    with pytest.raises(ValueError, match='artifact changed'):
        runner.campaign(
            project, tmp_path / 'tampered', path, max_hours=0.01, resume=third
        )


def test_expensive_campaign_can_be_planned_but_cannot_launch_under_two_hour_limit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = Path(__file__).resolve().parents[2]
    hardware = Hardware('test', 8, 32 * GIB, 'test', 1)
    monkeypatch.setattr(runner, 'detect', lambda: hardware)
    monkeypatch.setattr(runner, 'versions', lambda: {'runtime': 'test'})
    engines: tuple[Engine, ...] = ('brian', 'mlx')
    isolated = [
        runner.Completed(
            job=Job(engine, experiment, 9999),
            directory=tmp_path,
            trial_sha256='unused',
            wall_s=100.0,
            sampled_tree_peak_bytes=1024,
            memory_envelope_bytes=1024,
            retained_bytes=10000,
        )
        for experiment in runner.EXPERIMENTS
        for engine in engines
    ]
    profile = runner.Profile(
        hardware=hardware,
        allocation=allocation(1),
        isolated=isolated,
        coupled=[Sample(1, 100.0, 100.0)],
        source_sha256=sources(project),
        versions={'runtime': 'test'},
        threads=runner.THREADS,
        scope='control test',
        execution_identity={'brian': {'runtime': 'test'}, 'mlx': {'runtime': 'test'}},
    )
    path = tmp_path / 'profile.json'
    runner.write(path, profile)
    plan = runner.campaign(
        project, tmp_path / 'plan', path, max_hours=2, resume=None, plan_only=True
    )
    assert plan['remaining_jobs'] == 450
    assert not (tmp_path / 'plan/wave').exists()
    with pytest.raises(ValueError, match='explicit approval'):
        runner.campaign(project, tmp_path / 'blocked', path, max_hours=2, resume=None)
    assert not (tmp_path / 'blocked').exists()


@pytest.mark.parametrize(
    'field,value',
    [
        ('versions', {'runtime': 'wrong'}),
        ('python', 'wrong'),
        ('arrow_cpu_threads', 8),
        ('device', 'wrong'),
        ('MLX_ENABLE_TF32', '1'),
    ],
)
def test_worker_intake_rejects_mixed_runtime_fields(
    tmp_path: Path, field: str, value: object
) -> None:
    project, command, _, _ = setup_worker(tmp_path)
    job = Job('mlx', 'sugar', 0)
    row = runner.execute(
        project,
        tmp_path / 'wave',
        (job,),
        allocation(),
        deadline=perf_counter() + 20,
        command=command,
        memory=lambda: 128 * GIB,
        swap=lambda: 0,
    )[0]
    receipt = row.directory / 'trial.json'
    data = json.loads(receipt.read_text())
    data[field] = value
    receipt.write_text(json.dumps(data))
    with pytest.raises(
        ValueError, match='environment differs|device/precision differs'
    ):
        runner.verify(row.directory, job, sources(project))


def test_compatible_pilot_evidence_is_counted_once_without_another_worker(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project, command, launched, _ = setup_worker(tmp_path)
    job = Job('mlx', 'sugar', 0)
    measured = runner.execute(
        project,
        tmp_path / 'pilot-wave',
        (job,),
        allocation(1),
        deadline=perf_counter() + 20,
        command=command,
        memory=lambda: 128 * GIB,
        swap=lambda: 0,
    )[0]
    other = runner.Completed(
        job=Job('brian', 'sugar', 9999),
        directory=tmp_path,
        trial_sha256='unused',
        wall_s=0.1,
        sampled_tree_peak_bytes=1,
        memory_envelope_bytes=1,
    )
    profile = runner.Profile(
        hardware=Hardware('test', 8, 32 * GIB, 'test', 1),
        allocation=allocation(1),
        isolated=[measured, other],
        coupled=[Sample(1, 0.1, measured.wall_s)],
        source_sha256=sources(project),
        versions={'runtime': 'test'},
        threads=runner.THREADS,
        execution_identity={'brian': {'runtime': 'test'}, 'mlx': {'runtime': 'test'}},
        scope='control test',
    )
    path = tmp_path / 'profile.json'
    runner.write(path, profile)
    monkeypatch.setattr(runner, 'jobs', lambda: (job,))
    result = runner.campaign(
        project, tmp_path / 'run', path, max_hours=0.01, resume=None
    )
    assert result['execution_complete'] is True
    assert len(launched) == 1

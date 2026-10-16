import sys
from pathlib import Path
from types import ModuleType

import pytest

from tools.campaign_resources import (
    GIB,
    Allocation,
    Hardware,
    Sample,
    allocate,
    candidates,
    makespan,
    select,
)
from tools.run_tiered_campaign import jobs
from tools.tiered_trial import require_loaded_sources, sources


def test_m5_capacity_reserves_os_host_work_and_compiler_fanout() -> None:
    hardware = Hardware('Apple M5 Max', 18, 128 * GIB, 'Apple M5 Max', 40)
    result = allocate(hardware, 8 * GIB, 12 * GIB)
    assert result.cpu_workers == 7
    assert result.reserved_cpu_cores == 3
    assert result.gpu_workers == 1
    assert result.memory_headroom_bytes >= 12 * GIB


def test_memory_can_limit_workers_before_available_cores() -> None:
    hardware = Hardware('Apple M5 Max', 18, 128 * GIB, 'Apple M5 Max', 40)
    assert allocate(hardware, 40 * GIB, 12 * GIB).cpu_workers == 2
    with pytest.raises(ValueError, match='Insufficient'):
        allocate(hardware, 120 * GIB, 12 * GIB)


def test_measured_gpu_slowdown_can_make_one_cpu_worker_fastest() -> None:
    samples = (Sample(1, 50, 100), Sample(2, 55, 110), Sample(4, 65, 130))
    assert select(samples, cpu_jobs=150, gpu_jobs=300) == 1


def test_cpu_bottleneck_can_justify_measured_parallel_workers() -> None:
    samples = (Sample(1, 500, 100), Sample(2, 520, 100), Sample(4, 540, 120))
    assert select(samples, cpu_jobs=150, gpu_jobs=300) == 4
    assert candidates(7) == (1, 2, 4, 7)
    assert makespan((40.0,), 7) == 40.0
    assert makespan((10.0, 20.0, 30.0), 2) == 40.0


def test_loaded_allocation_cannot_create_two_gpu_workers() -> None:
    with pytest.raises(ValueError, match='exactly one GPU'):
        Allocation(1, 16 * GIB, 8 * GIB, GIB, GIB, 3, gpu_workers=2)


def test_source_inventory_rejects_an_editable_import_from_another_checkout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = Path(__file__).resolve().parents[2]
    foreign = tmp_path / 'foreign.py'
    foreign.write_text('value=1\n')
    module = ModuleType('fly_brain.foreign')
    module.__file__ = str(foreign)
    monkeypatch.setitem(sys.modules, 'fly_brain.foreign', module)
    with pytest.raises(ValueError, match='differs from the requested checkout'):
        require_loaded_sources(project, sources(project))


@pytest.mark.parametrize('silent_trials', (1, 30))
def test_campaign_cohorts_have_independent_seeds_and_unique_jobs(
    silent_trials: int,
) -> None:
    assert jobs() == jobs(30)
    selected = jobs(silent_trials)
    assert len(selected) == len(set(selected)) == 360 + 3 * silent_trials
    for experiment in ('sugar', 'p9', 'sugar-silenced', 'two-class', 'silent'):
        count = silent_trials if experiment == 'silent' else 30
        cpu = {
            job.trial
            for job in selected
            if job.experiment == experiment and job.engine == 'brian'
        }
        gpu = {
            job.trial
            for job in selected
            if job.experiment == experiment and job.engine == 'mlx'
        }
        assert cpu == set(range(1000, 1000 + count))
        assert gpu == set(range(count)) | set(range(2000, 2000 + count))
        assert not cpu & gpu


@pytest.mark.parametrize('count', (0, -1, 31, True))
def test_invalid_silent_cohort_size_is_rejected(count: int) -> None:
    with pytest.raises(ValueError, match='Silent cohort size'):
        jobs(count)

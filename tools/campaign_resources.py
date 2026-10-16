"""Capacity reservations and measured CPU/GPU campaign allocation."""

import heapq
import json
import math
import platform
import re
import subprocess
from dataclasses import dataclass

GIB = 1024**3


@dataclass(frozen=True)
class Hardware:
    chip: str
    cpu_cores: int
    memory_bytes: int
    gpu_name: str
    gpu_cores: int


@dataclass(frozen=True)
class Allocation:
    cpu_workers: int
    memory_budget_bytes: int
    memory_headroom_bytes: int
    cpu_worker_bytes: int
    gpu_worker_bytes: int
    reserved_cpu_cores: int
    gpu_workers: int = 1

    def __post_init__(self) -> None:
        if (
            self.gpu_workers != 1
            or min(
                self.cpu_workers,
                self.cpu_worker_bytes,
                self.gpu_worker_bytes,
                self.memory_budget_bytes,
                self.memory_headroom_bytes,
                self.reserved_cpu_cores,
            )
            < 1
        ):
            raise ValueError(
                'Allocation requires positive reservations and exactly one GPU worker'
            )


@dataclass(frozen=True)
class Sample:
    cpu_workers: int
    cpu_wave_s: float
    gpu_s: float

    def campaign_s(self, cpu_jobs: int, gpu_jobs: int) -> float:
        return max(cpu_jobs * self.cpu_wave_s / self.cpu_workers, gpu_jobs * self.gpu_s)


def command(*arguments: str) -> str:
    return subprocess.check_output(arguments, text=True, timeout=30).strip()


def detect() -> Hardware:
    if (platform.system(), platform.machine()) != ('Darwin', 'arm64'):
        raise RuntimeError('Campaign workers require Apple silicon/macOS')
    displays = json.loads(command('system_profiler', 'SPDisplaysDataType', '-json'))
    devices = displays['SPDisplaysDataType']
    if len(devices) != 1 or 'Apple' not in devices[0]['sppci_model']:
        raise RuntimeError('Qualify the actual Metal device before allocating workers')
    return Hardware(
        command('sysctl', '-n', 'machdep.cpu.brand_string'),
        int(command('sysctl', '-n', 'hw.ncpu')),
        int(command('sysctl', '-n', 'hw.memsize')),
        devices[0]['sppci_model'],
        int(devices[0]['sppci_cores']),
    )


def available_memory() -> int:
    statistics = command('vm_stat')
    page = re.search(r'page size of (\d+) bytes', statistics)
    if page is None:
        raise ValueError('Cannot read the native memory page size')
    pages = dict(re.findall(r'^([^:]+):\s+(\d+)\.', statistics, re.MULTILINE))
    return int(page[1]) * sum(
        int(pages[name])
        for name in ('Pages free', 'Pages inactive', 'Pages speculative')
    )


def allocate(
    hardware: Hardware,
    cpu_peak_bytes: int,
    gpu_peak_bytes: int,
    *,
    os_cores: int = 2,
    headroom_bytes: int | None = None,
) -> Allocation:
    if min(hardware.cpu_cores, cpu_peak_bytes, gpu_peak_bytes) <= 0 or os_cores < 1:
        raise ValueError('Allocation requires measured positive worker peaks')
    headroom = (
        max(8 * GIB, math.ceil(hardware.memory_bytes * 0.1))
        if headroom_bytes is None
        else headroom_bytes
    )
    if not 0 < headroom < hardware.memory_bytes:
        raise ValueError('Memory headroom must leave space for campaign workers')
    cpu_bytes, gpu_bytes = (
        math.ceil(peak * 1.25) for peak in (cpu_peak_bytes, gpu_peak_bytes)
    )
    budget = hardware.memory_bytes - headroom
    reserved = os_cores + 1
    workers = min(
        (hardware.cpu_cores - reserved) // 2,
        (budget - gpu_bytes) // cpu_bytes,
    )
    if workers < 1:
        raise ValueError('Insufficient CPU/memory capacity for concurrent engines')
    return Allocation(workers, budget, headroom, cpu_bytes, gpu_bytes, reserved)


def candidates(limit: int) -> tuple[int, ...]:
    if limit < 1:
        raise ValueError('At least one CPU worker is required')
    values = [1]
    while values[-1] < limit:
        values.append(min(limit, values[-1] * 2))
    return tuple(values)


def select(samples: tuple[Sample, ...], *, cpu_jobs: int, gpu_jobs: int) -> int:
    if (
        not samples
        or min(cpu_jobs, gpu_jobs) < 1
        or any(
            min(sample.cpu_workers, sample.cpu_wave_s, sample.gpu_s) <= 0
            or not math.isfinite(sample.cpu_wave_s + sample.gpu_s)
            for sample in samples
        )
    ):
        raise ValueError('Worker selection requires actual finite coupled samples')
    best = min(sample.campaign_s(cpu_jobs, gpu_jobs) for sample in samples)
    return min(
        sample.cpu_workers
        for sample in samples
        if sample.campaign_s(cpu_jobs, gpu_jobs) <= best * 1.03
    )


def makespan(durations: tuple[float, ...], workers: int) -> float:
    if workers < 1 or any(value < 0 or not math.isfinite(value) for value in durations):
        raise ValueError('Lane pricing requires finite durations and positive workers')
    lanes = [0.0] * workers
    for duration in durations:
        heapq.heapreplace(lanes, lanes[0] + duration)
    return max(lanes)

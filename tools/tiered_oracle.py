"""Independent SI float64 replay of the pinned Brian2 discrete model."""

from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike, NDArray

from fly_brain.simulation.models import Connectome

Float64 = NDArray[np.float64]
Boolean = NDArray[np.bool_]
Integer = NDArray[np.int64]


@dataclass(frozen=True)
class Frame:
    pre_v: Float64
    pre_g: Float64
    available: Boolean
    spikes: Boolean
    receiving: Boolean
    due_edges: Integer
    accepted_edges: Integer
    before_v: Float64
    before_g: Float64
    v: Float64
    g: Float64
    last_spike: Integer


class Oracle:
    def __init__(
        self,
        network: Connectome,
        targets: tuple[int, ...],
        silenced: tuple[int, ...] = (),
        *,
        voltage_mv: ArrayLike = -52,
        synaptic_mv: ArrayLike = 0,
        last_spike: ArrayLike = -100000000,
        threshold_only: bool = False,
    ) -> None:
        neurons = network.neuron_ids.size
        self.v = np.broadcast_to(voltage_mv, (neurons,)).astype(np.float64) * 0.001
        self.g = np.broadcast_to(synaptic_mv, (neurons,)).astype(np.float64) * 0.001
        self.last = np.broadcast_to(last_spike, (neurons,)).astype(np.int64).copy()
        self.targets = np.asarray(targets, dtype=np.int64)
        self.refractory = np.full(neurons, 22, dtype=np.int64)
        self.refractory[self.targets] = 0
        self.destinations = np.asarray(network.destinations)
        self.order = np.argsort(network.sources, kind='stable').astype(np.int64)
        degree = np.bincount(network.sources, minlength=neurons)
        self.offsets = np.concatenate(([0], np.cumsum(degree, dtype=np.int64)))
        self.weights = network.counts.astype(np.float64) * (0.275 * 0.001)
        self.weights[np.isin(network.sources, silenced)] = 0
        self.queue = np.zeros((19, neurons), dtype=np.bool_)
        self.counts = np.zeros(neurons, dtype=np.int64)
        self.tick = 0
        self.threshold_only = threshold_only
        dt, tau, membrane = np.float64(0.0001), np.float64(0.005), np.float64(0.020)
        self.a = np.exp(-dt / membrane)
        self.b = np.exp(-dt / tau)
        self.v0_term = -0.052 - (-0.052 * self.a)
        self.c = (
            ((tau / (membrane - tau)) * (-np.exp(dt / membrane) + np.exp(dt / tau)))
            * np.exp(-dt / membrane)
        ) * np.exp(-dt / tau)

    def advance(self, events: Boolean) -> Frame:
        if events.dtype != np.bool_ or events.shape != self.targets.shape:
            raise ValueError('Oracle input must contain one Boolean per channel')
        available = self.tick - self.last >= self.refractory
        pre_v = self.v.copy()
        pre_g = self.g.copy()
        if not self.threshold_only:
            pre_v[available] = (self.v0_term + (self.c * self.g + self.a * self.v))[
                available
            ]
            pre_g[available] = (self.b * self.g)[available]
        spikes = available & (pre_v > -0.045)
        receiving = available & ~spikes
        delayed = np.flatnonzero(self.queue[self.tick % 19])
        due = np.concatenate(
            [np.empty(0, dtype=np.int64)]
            + [self.order[self.offsets[i] : self.offsets[i + 1]] for i in delayed]
        )
        accepted = due[receiving[self.destinations[due]]]
        before_g = pre_g.copy()
        np.add.at(before_g, self.destinations[accepted], self.weights[accepted])
        before_v = pre_v.copy()
        for channel in np.flatnonzero(events):
            target = self.targets[channel]
            if receiving[target]:
                before_v[target] += 68.75 * 0.001
        self.v = np.where(spikes, -0.052, before_v)
        self.g = np.where(spikes, 0.0, before_g)
        self.last = np.where(spikes, self.tick, self.last)
        self.queue[self.tick % 19] = False
        self.queue[(self.tick + 18) % 19] = spikes
        self.counts += spikes
        self.tick += 1
        return Frame(
            pre_v,
            pre_g,
            available,
            spikes,
            receiving,
            due,
            accepted,
            before_v,
            before_g,
            self.v,
            self.g,
            self.last,
        )

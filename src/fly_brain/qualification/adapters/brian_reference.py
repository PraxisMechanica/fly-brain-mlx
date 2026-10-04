from collections.abc import Sequence
from textwrap import dedent
from typing import TypedDict

from brian2 import Hz, NeuronGroup, PoissonInput, Quantity, Synapses, ms, mV


class ReferenceParameters(TypedDict):
    v_0: Quantity
    v_rst: Quantity
    v_th: Quantity
    t_mbr: Quantity
    tau: Quantity
    t_rfc: Quantity
    t_dly: Quantity
    w_syn: Quantity
    r_poi: Quantity
    r_poi2: Quantity
    f_poi: int
    eqs: str
    eq_th: str
    eq_rst: str


def default_parameters() -> ReferenceParameters:
    return {
        'v_0': -52 * mV,
        'v_rst': -52 * mV,
        'v_th': -45 * mV,
        't_mbr': 20 * ms,
        'tau': 5 * ms,
        't_rfc': 2.2 * ms,
        't_dly': 1.8 * ms,
        'w_syn': 0.275 * mV,
        'r_poi': 100 * Hz,
        'r_poi2': 0 * Hz,
        'f_poi': 250,
        'eqs': dedent("""
            dv/dt = (v_0 - v + g) / t_mbr : volt (unless refractory)
            dg/dt = -g / tau               : volt (unless refractory)
            rfc                           : second
        """),
        'eq_th': 'v > v_th',
        'eq_rst': 'v = v_rst; w = 0; g = 0 * mV',
    }


def add_poisson_inputs(
    neu: NeuronGroup,
    exc: Sequence[int],
    exc2: Sequence[int],
    params: ReferenceParameters,
) -> list[PoissonInput]:
    """Add Poisson inputs to specified neurons."""
    pois: list[PoissonInput] = []
    for i in exc:
        p = PoissonInput(
            target=neu[i],
            target_var='v',
            N=1,
            rate=params['r_poi'],
            weight=params['w_syn'] * params['f_poi'],
        )
        neu[i].rfc = 0 * ms
        pois.append(p)
    for i in exc2:
        p = PoissonInput(
            target=neu[i],
            target_var='v',
            N=1,
            rate=params['r_poi2'],
            weight=params['w_syn'] * params['f_poi'],
        )
        neu[i].rfc = 0 * ms
        pois.append(p)
    return pois


def silence_neurons(syn: Synapses, slnc: Sequence[int]) -> None:
    """Set synapse weights to 0 for silenced neurons."""
    for i in slnc:
        syn.w[f' {i} == i'] = 0 * mV

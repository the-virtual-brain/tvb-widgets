# -*- coding: utf-8 -*-
#
# "TheVirtualBrain - Widgets" package
#
# (c) 2022-2025, TVB Widgets Team
#

from tvb.simulator.lab import *
from tvb.datatypes import time_series
import tvb.datatypes.time_series
import numpy as np
import math


def generate_ts_with_stimulus(length=5e3, cutoff=1e3, conn=None):
    if conn is None:
        conn = _generate_connectivity(76)

    weighting = np.zeros((76,))
    weighting[[14, 52, 11, 49]] = 0.1

    eqn_t = equations.PulseTrain()
    eqn_t.parameters['onset'] = 1.5e3
    eqn_t.parameters['T'] = 100.0
    eqn_t.parameters['tau'] = 50.0

    stimulus = patterns.StimuliRegion(
        temporal=eqn_t,
        connectivity=conn,
        weight=weighting)
    stimulus.configure_space()
    stimulus.configure_time(np.arange(0., 3e3, 2 ** -4))

    sim = simulator.Simulator(model=models.Generic2dOscillator(a=np.array([0.3]), tau=np.array([2])),
                              connectivity=conn,
                              coupling=coupling.Difference(a=np.array([7e-4])),
                              integrator=integrators.HeunStochastic(dt=0.5,
                                                                    noise=noise.Additive(nsig=np.array([5e-5]))),
                              monitors=(monitors.TemporalAverage(period=1.0),),
                              stimulus=stimulus,
                              simulation_length=length + cutoff,
                              ).configure()

    (tavg_time, tavg_data), = sim.run()
    cut_idx = int(math.ceil(cutoff / sim.monitors[0].period))

    tsr = tvb.datatypes.time_series.TimeSeriesRegion(data=tavg_data[cut_idx:],
                                                     time=tavg_time[cut_idx:],
                                                     connectivity=conn,
                                                     start_time=tavg_time[cut_idx] / 1000.0,
                                                     sample_period=sim.monitors[0].period / 1000.0,
                                                     sample_period_unit="s")
    # Fill the State Var names
    state_variable_dimension_name = tsr.labels_ordering[1]
    selected_vois = [sim.model.variables_of_interest[idx] for idx in sim.monitors[0].voi]
    tsr.labels_dimensions[state_variable_dimension_name] = selected_vois

    tsr.configure()
    return tsr


def generate_ts_with_mode_and_sv(length=5e3, cutoff=500, conn=None):
    if conn is None:
        conn = _generate_connectivity(76)
    jrm = models.JansenRit(mu=np.array([0.]), v0=np.array([6.]))
    monitor = monitors.TemporalAverage(period=2 ** -2)

    phi_n_scaling = (jrm.a * jrm.A * (jrm.p_max - jrm.p_min) * 0.5) ** 2 / 2.
    sigma = np.zeros(6)
    sigma[3] = phi_n_scaling

    sim = simulator.Simulator(model=jrm,
                              connectivity=conn,
                              coupling=coupling.SigmoidalJansenRit(a=np.array([10.0])),
                              integrator=integrators.HeunStochastic(dt=2 ** -4, noise=noise.Additive(nsig=sigma)),
                              monitors=(monitor,),
                              simulation_length=length + cutoff,
                              ).configure()

    (time_array, data_array), = sim.run()
    cut_idx = int(math.ceil(cutoff / monitor.period))

    tsr = time_series.TimeSeriesRegion(data=data_array[cut_idx:],
                                       time=time_array[cut_idx:],
                                       connectivity=conn,
                                       start_time=time_array[cut_idx] / 1000.0,
                                       sample_period=monitor.period / 1000,
                                       sample_period_unit="s")
    # Fill the State Var names
    state_variable_dimension_name = tsr.labels_ordering[1]
    selected_vois = [jrm.variables_of_interest[idx] for idx in monitor.voi]
    tsr.labels_dimensions[state_variable_dimension_name] = selected_vois

    tsr.configure()
    return tsr


def _generate_connectivity(no_of_regions):
    labels = np.array(['sig ' + str(i) for i in range(no_of_regions)])
    rng = np.random.default_rng(50)
    conn = connectivity.Connectivity(centres=rng.random(size=(no_of_regions, 3)),
                                     region_labels=labels,
                                     weights=rng.random(size=(no_of_regions, no_of_regions)),
                                     tract_lengths=rng.random(size=(no_of_regions, no_of_regions)))
    return conn

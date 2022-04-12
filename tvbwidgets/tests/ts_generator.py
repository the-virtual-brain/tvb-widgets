# -*- coding: utf-8 -*-
#
# "TheVirtualBrain - Widgets" package
#
# (c) 2022-2023, TVB Widgets Team
#

from tvb.simulator.lab import *
from tvb.datatypes import time_series
import tvb.datatypes.time_series
import numpy as np


def generate_ts_with_stimulus(length=5e3):
    conn = connectivity.Connectivity.from_file()

    # configure stimulus spatial pattern
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
    # Configure space and time
    stimulus.configure_space()
    stimulus.configure_time(np.arange(0., 3e3, 2 ** -4))

    sim = simulator.Simulator(
        model=models.Generic2dOscillator(a=np.array([0.3]), tau=np.array([2])),
        connectivity=conn,
        coupling=coupling.Difference(a=np.array([7e-4])),
        integrator=integrators.HeunStochastic(dt=0.5, noise=noise.Additive(nsig=np.array([5e-5]))),
        monitors=(
            monitors.TemporalAverage(period=1.0),
        ),
        stimulus=stimulus,
        simulation_length=length,
    ).configure()

    (tavg_time, tavg_data), = sim.run()
    tsr = tvb.datatypes.time_series.TimeSeriesRegion(data=tavg_data,
                                                     connectivity=conn,
                                                     sample_period=sim.monitors[0].period / 1000.0,
                                                     sample_period_unit="s")
    tsr.configure()
    return tsr


def generate_ts_with_mode_and_sv(length=1e3):
    jrm = models.JansenRit(mu=np.array([0.]), v0=np.array([6.]))
    monitor = monitors.TemporalAverage(period=2 ** -2)

    # the other aspects of the simulator are standard
    sim = simulator.Simulator(
        model=jrm,
        connectivity=connectivity.Connectivity.from_file(),
        coupling=coupling.SigmoidalJansenRit(a=np.array([10.0])),
        monitors=(monitor,),
        simulation_length=length,
    ).configure()

    # run it
    (time_array, data_array), = sim.run()
    tsr = time_series.TimeSeries(data=data_array,
                                 time=time_array,
                                 sample_period=monitor.period / 1000,
                                 sample_period_unit="s")
    tsr.configure()
    return tsr

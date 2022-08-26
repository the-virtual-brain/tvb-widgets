import numpy as np
from tvb.datatypes.connectivity import Connectivity
from tvb.simulator.coupling import Coupling, Linear
from tvb.simulator.integrators import HeunDeterministic, Integrator
from tvb.simulator.models.base import Model
from tvb.simulator.models.oscillator import Generic2dOscillator
from tvb.simulator.simulator import Simulator

from xai_components.base import InArg, OutArg, Component, xai_component


@xai_component
class ConnectivityComponent(Component):
    connectivity: OutArg[Connectivity]

    def __init__(self):
        self.done = False

        self.connectivity = OutArg(None)

    def execute(self, ctx) -> None:
        # imports
        from tvb.simulator.lab import connectivity

        self.connectivity.value = connectivity.Connectivity.from_file()

        # self.done = True


@xai_component
class LinearCouplingComponent(Component):
    float_a: InArg[float]
    float_b: InArg[float]

    linear_coupling: OutArg[Linear]

    def __init__(self):
        self.done = False

        self.float_a = InArg(None)
        self.float_b = InArg(None)
        self.linear_coupling = OutArg(None)

    def execute(self, ctx) -> None:
        # imports
        from tvb.simulator.lab import coupling

        a = self.float_a.value
        b = self.float_b.value

        linear_coupling = coupling.Linear(a=np.array([a]), b=np.array([b]))
        self.linear_coupling.value = linear_coupling


@xai_component
class Generic2dOscillatorComponent(Component):
    model: OutArg[Generic2dOscillator]

    def __init__(self):
        self.done = False

        self.model = OutArg(None)

    def execute(self, ctx) -> None:
        # imports
        from tvb.simulator.lab import models

        model = models.Generic2dOscillator()
        self.model.value = model


@xai_component
class HeunDeterministicComponent(Component):
    integrator: OutArg[HeunDeterministic]

    def __init__(self):
        self.done = False

        self.integrator = OutArg(None)

    def execute(self, ctx) -> None:
        # imports
        from tvb.simulator.lab import integrators

        integrator = integrators.HeunDeterministic()
        self.integrator.value = integrator


@xai_component
class MonitorsComponent(Component):
    monitors: OutArg[list]

    def __init__(self):
        self.done = False

        self.monitors = OutArg.empty()

    def execute(self, ctx) -> None:
        # imports
        from tvb.simulator.lab import monitors

        monitors_list = []
        temporal_average = monitors.TemporalAverage()

        monitors_list.append(temporal_average)
        self.monitors.value = monitors_list


@xai_component
class SimulatorComponent(Component):
    connectivity: InArg[Connectivity]
    coupling: InArg[Linear]
    model: InArg[Generic2dOscillator]
    integrator: InArg[HeunDeterministic]
    monitors: InArg[list]
    simulation_length: InArg[float]

    simulator: OutArg[Simulator]

    def __init__(self):
        self.done = False

        self.connectivity = InArg(None)
        self.coupling = InArg(None)
        self.model = InArg(None)
        self.integrator = InArg(None)
        self.monitors = InArg(None)
        self.simulation_length = InArg(None)
        self.simulator = OutArg(None)

    def execute(self, ctx) -> None:
        # imports
        from tvb.simulator import simulator
        sim = simulator.Simulator(
            connectivity=self.connectivity.value,
            coupling=self.coupling.value,
            model=self.model.value,
            integrator=self.integrator.value,
            monitors=self.monitors.value,
            simulation_length=self.simulation_length.value
        ).configure()

        self.simulator.value = sim
        print(self.simulator.value)

        self.done = True

from tvb.datatypes.connectivity import Connectivity
from tvb.datatypes.time_series import TimeSeries
from tvb.simulator.coupling import Linear
from tvb.simulator.integrators import HeunDeterministic
from tvb.simulator.models.oscillator import Generic2dOscillator

from xai_components.base import xai_component, Component, InArg, OutArg


@xai_component
class SimulatorForWidgetComponent(Component):
    connectivity: InArg[Connectivity]
    coupling: InArg[Linear]
    model: InArg[Generic2dOscillator]
    integrator: InArg[HeunDeterministic]
    monitors: InArg[list]
    simulation_length: InArg[float]

    # simulator: OutArg[Simulator]
    ts: OutArg[TimeSeries]

    def __init__(self):
        self.done = False

        self.connectivity = InArg(None)
        self.coupling = InArg(None)
        self.model = InArg(None)
        self.integrator = InArg(None)
        self.monitors = InArg(None)
        self.simulation_length = InArg(None)
        # self.simulator = OutArg(None)
        self.ts = OutArg(None)

    def execute(self, ctx) -> None:
        # imports
        from tvb.datatypes import time_series
        from tvb.simulator import simulator
        import math

        sim = simulator.Simulator(
            connectivity=self.connectivity.value,
            coupling=self.coupling.value,
            model=self.model.value,
            integrator=self.integrator.value,
            monitors=self.monitors.value,
            simulation_length=self.simulation_length.value
        ).configure()

        # self.simulator.value = sim
        # print(self.simulator.value)

        # generate TimeSeries
        (time, data), = sim.run()
        cutoff = 500
        cut_idx = int(math.ceil(cutoff / sim.monitors[0].period))

        tsr = time_series.TimeSeriesRegion(data=data[cut_idx:],
                                           time=time[cut_idx:],
                                           connectivity=sim.connectivity,
                                           start_time=time[cut_idx] / 1000.0,
                                           sample_period=sim.monitors[0].period / 1000,
                                           sample_period_unit="s")

        tsr.configure()
        self.ts.value = tsr


@xai_component
class TSWidgetComponent(Component):
    ts: InArg[TimeSeries]

    def __init__(self):
        self.done = False

        self.ts = InArg(None)

    def execute(self, ctx) -> None:
        # imports
        from tvbwidgets.ui.ts_widget import TimeSeriesWidget
        from IPython.utils import capture
        from IPython.display import display
        from IPython import get_ipython
        import matplotlib

        get_ipython().run_line_magic("matplotlib", "widget")
        print('BACKEND:' + matplotlib.get_backend())

        with capture.capture_output() as captured:
            ts_widget = TimeSeriesWidget()
            ts_widget.add_datatype(self.ts.value)
            display(ts_widget)
        captured()

        self.done = True

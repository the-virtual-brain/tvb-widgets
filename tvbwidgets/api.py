# -*- coding: utf-8 -*-
#
# "TheVirtualBrain - Widgets" package
#
# (c) 2022-2023, TVB Widgets Team
#

from .ui.phase_plane_widget import PhasePlaneWidget
from .ui.storage_widget import StorageWidget
from .ui.head_widget import HeadBrowser, HeadWidget, HeadWidgetConfig
from .ui.ts_widget import TimeSeriesWidget, TimeSeriesBrowser
from .ui.pse_widget import PSEWidget
from .ui.pse_launcher_widget import PSELauncher
from tvbwidgets.core.hpc.config import HPCConfig
from IPython.core.display_functions import display
from tvb.datatypes.time_series import TimeSeries


def plot_timeseries(data, sample_freq=None, ch_idx=None, backend='matplotlib'):
    """
    Plots a timeseries widget
    :param data: timeseries data as numpy array or TimeSeries object
    :param sample_freq: float
    :param ch_idx: Channels Index from the max 4D of the data. We assume time is on 0
    :param backend: plotting backend ('matplotlib' or 'plotly'), currently only matplotlib is supported (string)
    """

    if backend == 'matplotlib':
        tsw = TimeSeriesWidget()
        if isinstance(data, TimeSeries):
            tsw.add_datatype(data)
        else:
            tsw.add_data_array(data, sample_freq, ch_idx)
        display(tsw)
    elif backend == 'plotly':
        raise NotImplementedError('Plotly is not currently supported')
    else:
        raise ValueError('The chose backend is not supported, please choose between: "matplotlib" and "plotly"')

# -*- coding: utf-8 -*-
#
# "TheVirtualBrain - Widgets" package
#
# (c) 2022-2025, TVB Widgets Team
#

from .ui.connectivity_ipy.connectivity_widget import ConnectivityWidget
from .ui.connectivity_react.connectivity_widget import ConnectivityWidgetReact
from .ui.connectivity_matrix_editor_widget import ConnectivityMatrixEditor
from .ui.dicom_widget import DicomWidget
from .ui.phase_plane_widget import PhasePlaneWidget
from .ui.spacetime_widget import SpaceTimeVisualizerWidget
from .ui.storage_widget import StorageWidget
from .ui.head_widget import HeadBrowser, HeadWidget, HeadWidgetConfig
from .ui.ts.mne_ts_widget import TimeSeriesWidgetMNE
from .ui.ts.plotly_ts_widget import TimeSeriesWidgetPlotly
from .ui.ts.ts_widget_browser import TimeSeriesBrowser
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
        tsw = TimeSeriesWidgetMNE()
    elif backend == 'plotly':
        tsw = TimeSeriesWidgetPlotly()
    else:
        raise ValueError('The chose backend is not supported, please choose between: "matplotlib" and "plotly"')

    tsw.add_data(data=data, sample_freq=sample_freq, ch_idx=ch_idx)
    display(tsw)

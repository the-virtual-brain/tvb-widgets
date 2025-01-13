# -*- coding: utf-8 -*-
#
# "TheVirtualBrain - Widgets" package
#
# (c) 2022-2025, TVB Widgets Team
#

import ipywidgets as widgets
from tvb.datatypes.time_series import TimeSeries
from tvbwidgets.ui.ts.mne_ts_widget import TimeSeriesWidgetMNE
from tvbwidgets.ui.ts.plotly_ts_widget import TimeSeriesWidgetPlotly
from tvbwidgets.ui.widget_with_browser import TVBWidgetWithBrowser


class TimeSeriesBrowser(widgets.VBox, TVBWidgetWithBrowser):

    def __init__(self, collab=None, folder=None, selected_storage=0):
        super().__init__(**{'collab': collab, 'folder': folder, 'selected_storage': selected_storage})
        btn_mne = widgets.Button(description='View TS with MNE')
        btn_plotly = widgets.Button(description='View TS with Plotly')
        self.buttons = widgets.HBox([btn_mne, btn_plotly], layout=widgets.Layout(margin="0px 0px 0px 20px"))
        self.children = [self.storage_widget, self.buttons, self.message_label]

        def load_ts_for_mne(_):
            self.timeseries_widget = TimeSeriesWidgetMNE()
            self.children = [self.storage_widget, self.buttons, self.message_label, self.timeseries_widget]
            self.load_selected_file(TimeSeries, ('.h5', '.npz'))

        def load_ts_for_plotly(_):
            self.timeseries_widget = TimeSeriesWidgetPlotly()
            self.children = [self.storage_widget, self.buttons, self.message_label, self.timeseries_widget]
            self.load_selected_file(TimeSeries, ('.h5', '.npz'))

        btn_mne.on_click(load_ts_for_mne)
        btn_plotly.on_click(load_ts_for_plotly)

    def add_datatype(self, datatype):  # type: (TimeSeries) -> None
        # Maybe we want to go back to self.timeseries_widget.reset_data() (but that is currently only working for MNE)
        self.timeseries_widget.add_datatype(datatype)

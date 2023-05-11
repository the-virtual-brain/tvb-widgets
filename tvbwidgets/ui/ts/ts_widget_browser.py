# -*- coding: utf-8 -*-
#
# "TheVirtualBrain - Widgets" package
#
# (c) 2022-2023, TVB Widgets Team
#

import ipywidgets as widgets
from tvb.datatypes.time_series import TimeSeries
from tvbwidgets.ui.widget_with_browser import TVBWidgetWithBrowser


class TimeSeriesBrowser(widgets.VBox, TVBWidgetWithBrowser):

    def __init__(self, collab=None, folder=None):
        super().__init__(**{'collab': collab, 'folder': folder})
        timeseries_button = widgets.Button(description='View time series')
        self.buttons = widgets.HBox([timeseries_button], layout=widgets.Layout(margin="0px 0px 0px 20px"))
        self.timeseries_widget = TimeSeriesWidget()
        self.children = [self.storage_widget, self.buttons, self.message_label, self.timeseries_widget]

        def add_timeseries_datatype(_):
            self.load_selected_file(TimeSeries, ('.h5', '.npz'))

        timeseries_button.on_click(add_timeseries_datatype)

    def add_datatype(self, datatype):  # type: (TimeSeries) -> None
        self.timeseries_widget.reset_data()
        self.timeseries_widget.add_datatype(datatype)
# -*- coding: utf-8 -*-
#
# "TheVirtualBrain - Widgets" package
#
# (c) 2022-2023, TVB Widgets Team
#

from tvbwidgets.ui.base_widget import TVBWidget
import ipywidgets as widgets
import numpy as np
import os


class TimeSeriesWidget(widgets.VBox, TVBWidget):
    def __init__(self, **kwargs):

        self.fig = None

        data = kwargs.get('data', None)
        self.data = data

        self.button1 = widgets.Button(description="View")
        self.button2 = widgets.Button(description="Model")
        self.output = widgets.Output()
        self.var = True
        self.checkboxes_list = []

        def view_action(s):
            self.fig.mne.picks = np.array([0])
            self.fig.mne.n_channels = len(self.fig.mne.picks)

            self.fig._update_picks()
            self.fig._update_trace_offsets()
            self.fig._update_vscroll()
            self.fig._redraw(annotations=True)

        self.button1.on_click(view_action)

        self.create_checkbox_list()
        self.region_box = widgets.HBox(self.checkboxes_list)

        items = [self.button1, self.button2, self.region_box, self.output]
        grid = widgets.GridBox(items)

        super().__init__([grid], **kwargs)

    def create_fig(self):
        with self.output:
            self.fig.show()

    def create_checkbox_list(self):
        os.write(1, f"In create_checkbox_list()\n".encode())
        self.checkboxes = dict()
        labels = self.data.ch_names
        for label in labels:
            self.checkboxes[label] = widgets.Checkbox(value=True,
                                                      description=label,
                                                      disabled=False,
                                                      indent=False)
            self.checkboxes[label].observe(self.update_ts, names="value", type="change")
            self.checkboxes_list.append(self.checkboxes[label])

    def update_ts(self, val):
        os.write(1, f"{val}\n".encode())
        channels = self.fig.mne.ch_order
        picks = []
        ch_names = list(self.fig.mne.ch_names)
        for cb in list(self.checkboxes.values()):
            if cb.value == True:
                index = ch_names.index(cb.description)
                picks.append(index)

        ch_start = self.fig.mne.ch_start
        ch_start_index = picks.index(ch_start)
        for i in range(len(picks)):
            if ch_start in picks:
                break
            else:
                ch_start_index += 1
                ch_start = picks[ch_start_index]

        self.fig.mne.ch_start = ch_start
        self.fig.mne.picks = np.array(picks[ch_start_index:(ch_start_index + len(self.fig.mne.n_channels))])
        self.fig.mne.n_channels = len(self.fig.mne.picks)

        self.fig._update_picks()
        self.fig._update_trace_offsets()
        self.fig._update_vscroll()
        self.fig._redraw(annotations=True)

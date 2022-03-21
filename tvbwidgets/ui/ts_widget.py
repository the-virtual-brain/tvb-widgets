# -*- coding: utf-8 -*-
#
# "TheVirtualBrain - Widgets" package
#
# (c) 2022-2023, TVB Widgets Team
#
import ipywidgets as widgets
import mne
import numpy as np
import os

from tvb.datatypes.time_series import TimeSeries
from tvbwidgets.ui.base_widget import TVBWidget


class TimeSeriesWidget(widgets.VBox, TVBWidget):
    def __init__(self, data, **kwargs):
        self.fig = None

        # data
        self.data = data
        self.data_type = None
        self.ch_names = []
        self.ch_order = []
        self.displayed_period = 0
        self.no_channels = 30
        self.raw = None

        self.configure_ts_widget()

        # UI elements
        self.output = widgets.Output(layout=widgets.Layout(border='solid'))

        # checkboxes region
        self.checkboxes = dict()
        self.checkboxes_list = []
        self.create_checkbox_list()
        self.checkboxes_region = widgets.HBox(children=self.checkboxes_list,
                                              layout=widgets.Layout(height='400px', width='auto'))
        self.accordion = widgets.Accordion(children=[self.checkboxes_region], layout=widgets.Layout(width='40%'))
        self.accordion.set_title(0, 'Channels')

        # buttons region
        self.select_all_btn = widgets.Button(description="Select all")
        self.select_all_btn.on_click(self.select_all)
        self.unselect_all_btn = widgets.Button(description="Unselect all")
        self.unselect_all_btn.on_click(self.unselect_all)
        self.buttons_box = widgets.HBox(children=[self.select_all_btn, self.unselect_all_btn])

        super().__init__(**kwargs)

    # ====================================== CONFIGURATION =============================================================
    def configure_ts_widget(self):
        if isinstance(self.data, TimeSeries):
            self.data_type = TimeSeries
            self.configure_ch_names_ts()
            self.configure_displayed_period_ts()
            self.configure_ch_order_ts()
            self.create_raw_from_ts()
            os.write(1, f"It's a TVB TimeSeries!\n".encode())
        elif isinstance(self.data, np.ndarray):
            self.data_type = np.ndarray
            os.write(1, f"It's a numpy array!\n".encode())

    # configure channel names when data is a TVB TimeSeries object
    def configure_ch_names_ts(self):
        if not self.ch_names:
            no_channels = self.data.shape[2]  # number of channels is on axis 2
            self.ch_names = list(range(no_channels))
            self.ch_names = [str(ch) for ch in list(range(no_channels))]  # list should contain str

    def configure_displayed_period_ts(self):
        total_period = self.data.summary_info()['Length']
        self.displayed_period = total_period / 10  # chose to display a tenth of the total duration

    def configure_ch_order_ts(self):
        if not self.ch_order:
            no_channels = self.data.shape[2]  # number of channels is on axis 2
            self.ch_order = list(range(no_channels))  # the order should be the order in which they are provided

    # ======================================= RAW OBJECT ==============================================================
    def create_raw_from_ts(self):
        # create Info object for Raw object
        raw_info = mne.create_info(self.ch_names, sfreq=self.data.sample_rate)

        # TODO: currently taking only 1st value for state var and mode; this should be corrected
        data_for_raw = self.data.data[:, 0, :, 0]
        data_for_raw = np.swapaxes(data_for_raw, 0, 1)
        raw = mne.io.RawArray(data_for_raw, raw_info)
        self.raw = raw

    # ========================================== BUTTONS ===============================================================
    # buttons methods
    def unselect_all(self, btn):
        for cb_name in self.checkboxes:
            self.checkboxes[cb_name].value = False

    def select_all(self, btn):
        for cb_name in self.checkboxes:
            self.checkboxes[cb_name].value = True

    # =========================================== PLOT =================================================================
    def get_widget(self):
        def update_on_plot_interaction(event):
            """
            Function that updates the checkboxes when the user navigates through the plot
            using either the mouse or the keyboard
            """
            picks = list(self.fig.mne.picks)
            for ch in picks:
                ch_name = self.fig.mne.ch_names[ch]
                cb = self.checkboxes[ch_name]
                if cb.value == False:
                    cb.value = True

        # create the plot
        self.fig = self.raw.plot(duration=self.displayed_period, n_channels=self.no_channels, clipping=None, show=False)
        self.fig.mne.ch_order = self.ch_order

        # add custom widget handling on keyboard and mouse events
        self.fig.canvas.mpl_connect('key_press_event', update_on_plot_interaction)
        self.fig.canvas.mpl_connect('button_press_event', update_on_plot_interaction)

        # display the plot
        with self.output:
            self.fig

        items = [self.accordion, self.buttons_box, self.output]
        grid = widgets.GridBox(items)
        return grid

    # ======================================== CHECKBOXES ==============================================================
    def create_checkbox_list(self):
        checkboxes_stack = []
        labels = self.ch_names
        for i, label in enumerate(labels):
            self.checkboxes[label] = widgets.Checkbox(value=True,
                                                      description=str(label),
                                                      disabled=False,
                                                      indent=False)
            self.checkboxes[label].observe(self.update_ts, names="value", type="change")
            if i and i % 38 == 0:
                self.checkboxes_list.append(widgets.VBox(children=checkboxes_stack))
                checkboxes_stack = []
            checkboxes_stack.append(self.checkboxes[label])
        self.checkboxes_list.append(widgets.VBox(children=checkboxes_stack))

    def update_ts(self, val):
        ch_names = list(self.fig.mne.ch_names)
        os.write(1, f"{val['owner']}\n".encode())

        # check if newly checked option is before current ch_start in the channels list
        if val['old'] == False and val['new'] == True:
            ch_name = val['owner'].description
            ch_number = ch_names.index(ch_name)
            ch_changed_index = list(self.fig.mne.ch_order).index(ch_number)
            if ch_changed_index < self.fig.mne.ch_start:
                self.fig.mne.ch_start = ch_changed_index

        # divide list of all channels into checked(picked) and unchecked(not_picked) channels
        picks = []
        not_picked = []
        for cb in list(self.checkboxes.values()):
            ch_number = ch_names.index(cb.description)  # get the number repres. of checked/uncheched channel
            if cb.value == True:
                picks.append(ch_number)  # list with number representation of channels
            else:
                not_picked.append(ch_number)

        if not picks:
            self.fig.mne.picks = picks
            self.fig.mne.n_channels = 0
            self.update_fig()
            return

        # if not enough values are checked, force the plot to display less channels
        n_channels = self.fig.mne.n_channels
        if (len(picks) < n_channels) or (n_channels < len(picks) <= self.no_channels):
            self.fig.mne.n_channels = len(picks)
        else:
            self.fig.mne.n_channels = self.no_channels

        # order list of checked channels according to self.fig.mne.ch_order
        ch_order_filtered = [x for x in self.fig.mne.ch_order if x not in not_picked]

        ch_start = self.fig.mne.ch_start
        ch_start_number = self.fig.mne.ch_order[ch_start]
        if ch_start_number not in ch_order_filtered:  # if first channel was unchecked
            ch_start = self.get_next_checked_channel(ch_start, ch_order_filtered, list(self.fig.mne.ch_order))

        self.fig.mne.ch_start = ch_start
        ch_start_number = self.fig.mne.ch_order[self.fig.mne.ch_start]
        ch_start_index = ch_order_filtered.index(ch_start_number)

        new_picks = np.array(ch_order_filtered[ch_start_index:(ch_start_index + self.fig.mne.n_channels)])
        self.fig.mne.picks = new_picks
        # self.fig.mne.n_channels = len(self.fig.mne.picks)
        ch_start_index = list(self.fig.mne.ch_order).index(new_picks[0])
        self.fig.mne.ch_start = ch_start_index

        self.update_fig()

    def get_next_checked_channel(self, ch_start, checked_list, ch_order):
        for i in range(len(ch_order)):
            ch_start += 1
            new_ch_start_number = ch_order[ch_start]        # get the number representation of next first channel
            if new_ch_start_number in checked_list:
                break
        return ch_start

    def update_fig(self):
        self.fig._update_trace_offsets()
        self.fig._update_vscroll()
        self.fig._redraw(annotations=True)

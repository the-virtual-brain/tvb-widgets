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

        # data
        data = kwargs.get('data', None)
        self.data = data
        self.no_channels = 30

        self.output = widgets.Output()

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

    # buttons methods
    def unselect_all(self, btn):
        for cb_name in self.checkboxes:
            self.checkboxes[cb_name].value = False

    def select_all(self, btn):
        for cb_name in self.checkboxes:
            self.checkboxes[cb_name].value = True

    # plot methods
    def create_fig(self):
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
        self.fig = self.data.plot(duration=5, n_channels=self.no_channels, clipping=2, show=False)

        # add custom widget handling on keyboard and mouse events
        self.fig.canvas.mpl_connect('key_press_event', update_on_plot_interaction)
        self.fig.canvas.mpl_connect('button_press_event', update_on_plot_interaction)

        # display the plot
        with self.output:
            self.fig

        items = [self.accordion, self.buttons_box, self.output]
        grid = widgets.GridBox(items)
        return grid

    # checkboxes methods
    def create_checkbox_list(self):
        checkboxes_stack = []
        labels = self.data.ch_names
        for i, label in enumerate(labels):
            self.checkboxes[label] = widgets.Checkbox(value=True,
                                                      description=label,
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

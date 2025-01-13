# -*- coding: utf-8 -*-
#
# "TheVirtualBrain - Widgets" package
#
# (c) 2022-2025, TVB Widgets Team
#

import os
import mne
import numpy as np
import ipywidgets as widgets
import matplotlib.pyplot as plt
from IPython.core.display_functions import display
from tvbwidgets.core.ini_parser import parse_ini_file
from tvbwidgets.ui.ts.base_ts_widget import TimeSeriesWidgetBase

mne.set_config('MNE_BROWSER_BACKEND', 'matplotlib')


class TimeSeriesWidgetMNE(TimeSeriesWidgetBase):
    """ Actual TimeSeries Widget """

    def __init__(self, **kwargs):

        self.fig = None
        self.data = None
        self.ch_names = []
        self.ch_order = []
        self.ch_types = []
        self.displayed_period = 0
        self.no_channels = 30
        self.raw = None
        self.sample_freq = 0
        self.picked_channels = []
        self.plot_psd_toggle = None

        self.output = widgets.Output(layout=widgets.Layout(width='auto'))
        annotation_area = self._create_annotation_area()
        self.instr_area = self._create_instructions_region()
        self.title_area = widgets.HBox(children=[self.instr_area])

        self.checkboxes = dict()
        super().__init__([self.output, annotation_area, self.title_area], layout=self.DEFAULT_BORDER)
        self.logger.info("TimeSeries Widget initialized")

    # =========================================== SETUP ================================================================
    def reset_data(self):
        self.data = None
        self.title_area.children = [self.instr_area]

    def _populate_from_data_wrapper(self, data_wrapper):
        super()._populate_from_data_wrapper(data_wrapper=data_wrapper)
        self.channels_area = self._create_channel_selection_area(data_wrapper, 7)
        self.title_area.children += (self.channels_area,)
        self._redraw()

    # ======================================== CHANNEL VALUE AREA ======================================================
    def _create_annotation_area(self):
        title_label = widgets.Label(value='Channel values:')
        self.channel_val_area = widgets.VBox()
        annot_area = widgets.HBox(children=[title_label, self.channel_val_area], layout={'height': '70px',
                                                                                         'padding': '0 0 0 100px'})
        return annot_area

    # ===================================== INSTRUCTIONS DROPDOWN ======================================================
    @staticmethod
    def _create_instructions_region():
        instr_list, key_list, val_list = [], [], []
        help_text = parse_ini_file(os.path.join(os.path.dirname(__file__), "ts_widget_help.ini"))

        for key, value in help_text.items():
            key_label = widgets.Label(value=key)
            val_label = widgets.Label(value=value)
            key_list.append(key_label)
            val_list.append(val_label)

        instr_list.append(widgets.VBox(children=key_list))
        instr_list.append(widgets.VBox(children=val_list))
        instr_region = widgets.HBox(children=instr_list)
        instr_accordion = widgets.Accordion(children=[instr_region], selected_index=None,
                                            layout=widgets.Layout(width='40%'))
        instr_accordion.set_title(0, 'Keyboard shortcuts')
        return instr_accordion

    # =========================================== PLOT =================================================================
    def update_on_plot_interaction(self, _):
        """
        Function that updates the checkboxes when the user navigates through the plot
        using either the mouse or the keyboard
        """
        picks = list(self.fig.mne.picks)
        for ch in picks:
            ch_name = self.fig.mne.ch_names[ch]
            cb = self.checkboxes[ch_name]
            if not cb.value:
                cb.value = True
        self._update_fig()

    def hover(self, event):
        """ Display the channel value when hovering over the plot"""
        self.channel_val_area.children = []

        values = []  # list of label values for channels we are hovering over
        x = event.xdata  # time unit (s, ms) we are hovering over
        lines = self.fig.mne.traces  # all currently visible channels
        sel1, sel2 = self._get_selection_values()
        if event.inaxes == self.fig.mne.ax_main:
            for line in lines:
                if line.contains(event)[0]:
                    line_index = lines.index(line)  # channel index among displayed channels
                    ch_index = self.fig.mne.picks[line_index]  # channel index among all channels
                    ch_name = self.fig.mne.ch_names[ch_index]

                    ch_value = self.data.get_hover_channel_value(x, ch_index, sel1, sel2)
                    label_val = f'{ch_name}: {ch_value}'
                    values.append(label_val)
            for v in values:
                val_label = widgets.Label(value=v)
                self.channel_val_area.children += (val_label,)

    def _redraw(self, toggle_psd=False):
        # display the plot
        with plt.ioff():
            with self.output:
                if toggle_psd and self.plot_psd_toggle.value:
                    self.output.clear_output(wait=True)
                    self.raw.plot_psd(picks="all")
                    display(self.fig.canvas)
                    return
                elif toggle_psd:
                    self.output.clear_output(wait=True)
                    display(self.fig.canvas)
                    return

            # create the plot
            self.fig = self.raw.plot(duration=self.displayed_period, n_channels=self.no_channels, show_first_samp=True,
                                     clipping=None, show=False)
            self.fig.set_size_inches(11, 5)
            # self.fig.figure.canvas.set_window_title('TimeSeries plot')
            self.fig.mne.ch_order = self.ch_order
            self.fig.mne.ch_types = np.array(self.ch_types)

            # add custom widget handling on keyboard and mouse events
            self.fig.canvas.mpl_connect('key_press_event', self.update_on_plot_interaction)
            self.fig.canvas.mpl_connect('button_press_event', self.update_on_plot_interaction)
            self.fig.canvas.mpl_connect("motion_notify_event", self.hover)
            self.picked_channels = list(self.fig.mne.ch_names)
            with self.output:
                self.output.clear_output(wait=True)
                if not toggle_psd and self.plot_psd_toggle.value:
                    self.raw.plot_psd(picks="all")
                display(self.fig.canvas)

    # ======================================== CHANNELS  ==============================================================
    def _create_channel_selection_area(self, array_wrapper, no_checkbox_columns=7):
        # type: (ABCDataWrapper) -> widgets.Accordion
        """ Create the whole channel selection area: Select/Unselect all btns, State var. & Mode selection
            and Channel checkboxes
        """
        # checkboxes region
        checkboxes_region = self._create_checkboxes(array_wrapper=array_wrapper,
                                                    no_checkbox_columns=no_checkbox_columns)
        checkboxes_region.layout = widgets.Layout(width='590px', height='max-content')
        labels = array_wrapper.get_channels_info()[0]
        for label in labels:
            self.checkboxes[label].observe(self._update_ts, names="value", type="change")

        # select/unselect all buttons
        select_all_btn, unselect_all_btn = self._create_select_unselect_all_buttons()
        self.channel_color = widgets.ToggleButton(value=False, description="Multi-Color", disabled=False,
                                                  button_style='', tooltip='Multi-Color', icon='check',
                                                  layout=self.BUTTON_STYLE)

        def update_channels_color(change):
            if change['type'] != 'change' or change['name'] != 'value':
                return

            self.channel_color.value = change["new"]
            self._update_fig()

        self.channel_color.observe(update_channels_color)
        self.plot_psd_toggle = widgets.ToggleButton(value=False, description="Power Spectral Density", disabled=False,
                                                    button_style='', tooltip='Power Spectral Density', layout=self.BUTTON_STYLE)

        def update_to_plot_psd(change):
            if change['type'] != 'change' or change['name'] != 'value':
                return

            self.plot_psd_toggle.value = change["new"]
            self._redraw(True)

        self.plot_psd_toggle.observe(update_to_plot_psd)
        actions = [select_all_btn, unselect_all_btn]

        # select dimensions buttons (state var. & mode)
        actions.extend(self._create_dim_selection_buttons(array_wrapper=array_wrapper))

        # add all buttons to channel selection area
        channels_region = widgets.VBox(children=[widgets.HBox(actions),
                                                 widgets.HBox(children=[self.channel_color, self.plot_psd_toggle]),
                                                 checkboxes_region])
        channels_area = widgets.Accordion(children=[channels_region], selected_index=None,
                                          layout=widgets.Layout(width='50%'))
        channels_area.set_title(0, 'Channels')
        return channels_area

    def _dimensions_selection_update(self, _):
        # update self.raw and linked parts
        super()._dimensions_selection_update(_)

        # update plot
        self.fig = self.raw.plot(duration=self.displayed_period,
                                 n_channels=self.no_channels,
                                 clipping=None, show=False)
        self.fig.set_size_inches(11, 5)
        self._redraw()

        self.add_colors(self.channel_color.value)
        # refresh the checkboxes if they were unselected
        for cb_name in self.checkboxes:
            self.checkboxes[cb_name].value = True

    def _update_ts(self, val):
        ch_names = list(self.fig.mne.ch_names)
        self.logger.debug("Update_ts is called for channels " + str(ch_names))

        # check if newly checked option is before current ch_start in the channels list
        if (val['old'] is False) and (val['new'] is True):
            ch_name = val['owner'].description
            ch_number = ch_names.index(ch_name)
            ch_changed_index = list(self.fig.mne.ch_order).index(ch_number)
            if ch_changed_index < self.fig.mne.ch_start:
                self.fig.mne.ch_start = ch_changed_index

        # divide list of all channels into checked(picked) and unchecked(not_picked) channels
        picks = []
        not_picked = []
        self.picked_channels = []
        for cb in list(self.checkboxes.values()):
            ch_number = ch_names.index(cb.description)  # get the number representation of checked/unchecked channel
            if cb.value:
                picks.append(ch_number)  # list with number representation of channels
                self.picked_channels.append(cb.description)
            else:
                not_picked.append(ch_number)

        # for unselect all
        if not picks:
            self.fig.mne.picks = picks
            self.fig.mne.n_channels = 0
            self._update_fig(True)
            return

        # if not enough values are checked, force the plot to display less channels
        n_channels = self.fig.mne.n_channels
        if (len(picks) < n_channels) or (n_channels < len(picks) <= self.no_channels):
            self.fig.mne.n_channels = len(picks)
        else:
            self.fig.mne.n_channels = self.no_channels

        # order list of checked channels according to ordering rule (self.fig.mne.ch_order)
        ch_order_filtered = [x for x in self.fig.mne.ch_order if x not in not_picked]

        ch_start = self.fig.mne.ch_start
        ch_start_number = self.fig.mne.ch_order[ch_start]
        if ch_start_number not in ch_order_filtered:  # if first channel was unchecked
            ch_start = self._get_next_checked_channel(ch_start, ch_order_filtered, list(self.fig.mne.ch_order))

        self.fig.mne.ch_start = ch_start
        ch_start_number = self.fig.mne.ch_order[self.fig.mne.ch_start]
        ch_start_index = ch_order_filtered.index(ch_start_number)

        new_picks = np.array(ch_order_filtered[ch_start_index:(ch_start_index + self.fig.mne.n_channels)])
        self.fig.mne.n_channels = len(new_picks)  # needed for WID-66
        self.fig.mne.picks = new_picks
        ch_start_index = list(self.fig.mne.ch_order).index(new_picks[0])
        self.fig.mne.ch_start = ch_start_index

        self._update_fig()

    @staticmethod
    def _get_next_checked_channel(ch_start, checked_list, ch_order):
        for _ in range(len(ch_order)):
            ch_start += 1
            new_ch_start_number = ch_order[ch_start]  # get the number representation of next first channel
            if new_ch_start_number in checked_list:
                break
        return ch_start

    def _update_fig(self, unselect_all_flag=False):
        self.fig._update_trace_offsets()
        self.fig._update_vscroll()
        try:
            if self.channel_color.value:
                with self.output:
                    if not unselect_all_flag:
                        self.fig._redraw(annotations=True)
                        self.add_colors(self.channel_color.value)
                    else:
                        self.fig._redraw(update_data=False)
            else:
                self.fig._redraw(annotations=True)
        except ValueError:
            self.fig._redraw(update_data=False)

    def add_colors(self, color_on):
        """
        Function to add colors to channels
        """
        if color_on:
            colors = ['red', 'green', 'blue', 'black', 'orange', 'purple', 'pink', 'cyan', 'olive', 'brown'] * \
                     int(len(self.picked_channels)/10)
        else:
            colors = ['black'] * int(len(self.picked_channels))
        fig_color = self.fig.axes[0]
        bad_channels = self.fig.mne.info["bads"]
        for nl, (chan, color) in enumerate(zip(self.picked_channels, colors)):
            if nl < self.fig.mne.n_channels and chan not in bad_channels:
                line = fig_color.get_lines()[nl + 1]
                line.set_color(color)

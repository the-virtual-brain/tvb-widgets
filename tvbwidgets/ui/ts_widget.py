# -*- coding: utf-8 -*-
#
# "TheVirtualBrain - Widgets" package
#
# (c) 2022-2023, TVB Widgets Team
#
import ipywidgets as widgets
import math
import matplotlib.pyplot as plt
import mne
import numpy as np
import os

from collections import OrderedDict
from IPython.core.display_functions import display
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
        self.ch_types = []
        self.displayed_period = 0
        self.no_channels = 30
        self.selected_state_var = None
        self.selected_mode = None
        self.raw = None

        self.configure_ts_widget()

        # UI elements
        self.output = widgets.Output(layout=widgets.Layout(width='auto'))

        # checkboxes region
        self.checkboxes = dict()
        self.checkboxes_list = []
        self.create_checkbox_list()
        self.checkboxes_region = widgets.HBox(children=self.checkboxes_list,
                                              layout=widgets.Layout(height='250px'))
        self.accordion = widgets.Accordion(children=[self.checkboxes_region], layout=widgets.Layout(width='40%'))
        self.accordion.set_title(0, 'Channels')

        # buttons region
        self.select_all_btn = widgets.Button(description="Select all")
        self.select_all_btn.on_click(self.select_all)
        self.unselect_all_btn = widgets.Button(description="Unselect all")
        self.unselect_all_btn.on_click(self.unselect_all)

        # instructions region
        self.instr_list = []
        self.create_instructions()
        self.instr_region = widgets.HBox(children=self.instr_list)
        self.instr_accordion = widgets.Accordion(children=[self.instr_region], selected_index=None)
        self.instr_accordion.set_title(0, 'Keyboard shortcuts')

        # select dimensions region
        self.create_state_var_selection()
        self.state_var_accordion = widgets.Accordion(children=[self.state_var_radio_btn], selected_index=None)
        self.state_var_accordion.set_title(0, 'State variable')
        self.create_mode_selection()
        self.mode_accordion = widgets.Accordion(children=[self.mode_radio_btn], selected_index=None)
        self.mode_accordion.set_title(0, 'Mode')

        self.buttons_box = widgets.HBox(children=[self.select_all_btn, self.unselect_all_btn, self.instr_accordion,
                                                  self.state_var_accordion, self.mode_accordion])
        super().__init__(**kwargs)

    # ====================================== CONFIGURATION =============================================================
    def configure_ts_widget(self):
        if isinstance(self.data, TimeSeries):
            self.data_type = TimeSeries
            self.configure_ch_names_ts()
            self.configure_displayed_period_ts()
            self.configure_ch_order_ts()
            self.configure_ch_types_ts()
            self.create_raw_from_ts()
            os.write(1, f"It's a TVB TimeSeries!\n".encode())
        elif isinstance(self.data, np.ndarray):
            self.data_type = np.ndarray
            os.write(1, f"It's a numpy array!\n".encode())

    # configure channel names when data is a TVB TimeSeries object
    def configure_ch_names_ts(self):
        no_channels = self.data.shape[2]  # number of channels is on axis 2
        self.ch_names = list(range(no_channels))
        self.ch_names = [str(ch) for ch in list(range(no_channels))]  # list should contain str

    def configure_displayed_period_ts(self):
        total_period = self.data.summary_info()['Length']
        self.displayed_period = total_period / 10  # chose to display a tenth of the total duration

    def configure_ch_order_ts(self):
        no_channels = self.data.shape[2]  # number of channels is on axis 2
        self.ch_order = list(range(no_channels))  # the order should be the order in which they are provided

    def configure_ch_types_ts(self):
        types = ['misc' for x in self.ch_names]
        self.ch_types = types

    # ======================================= RAW OBJECT ===============================================================
    def create_raw_from_ts(self):
        # create Info object for Raw object
        raw_info = mne.create_info(self.ch_names, sfreq=self.data.sample_rate)

        valid_state_var = self.selected_state_var is not None
        valid_mode = self.selected_mode is not None
        if not (valid_state_var and valid_state_var):       # when plot is drawn for first time
            data_for_raw = self.data.data[:, 0, :, 0]
        else:
            state_var = self.selected_state_var if valid_state_var else 0
            mode = self.selected_mode if valid_mode else 0
            data_for_raw = self.data.data[:, state_var, :, mode]

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

    # ===================================== INSTRUCTIONS DROPDOWN ======================================================
    def create_instructions(self):
        help_text = OrderedDict([
            ('NAVIGATION', ' '),
            ('→', f'Scroll ¼ right (scroll full window with Shift + →)'),
            ('←', f'Scroll ¼ left (scroll full window with Shift + ←)'),
            ('Home (fn + ← for Mac)', 'Show shorter time window'),
            ('End (fn + → for Mac)', 'Show longer time window'),
            ('↑', f'Scroll up (channels)'),
            ('↓', f'Scroll down (channelss)'),
            ('Page up (fn + ↑ for Mac)', 'Increase number of visible channels'),
            ('Page down (fn + ↓ for Mac)', 'Decrease number of visible channels'),
            ('SIGNAL TRANSFORMATIONS', ' '),
            ('+ or =', 'Increase signal scaling'),
            ('-', 'Decrease signal scaling'),
            ('b', 'Toggle butterfly mode'),
            ('d', 'Toggle DC removal'),
            ('USER INTERFACE', ' '),
            ('a', 'Toggle annotation mode'),
            ('shift+j', 'Toggle all SSPs'),
            ('p', 'Toggle draggable annotations'),
            ('s', 'Toggle scalebars'),
            ('z', 'Toggle scrollbars'),
            ('esc', 'Close focused figure or dialog window'),
            ('MOUSE INTERACTION', ' '),
            (f'Left-click channel name', 'Mark/unmark bad channel'),
            (f'Left-click channels data', 'Mark/unmark bad channel'),
            ('Left-click-and-drag on plot', 'Add annotation (in annotation mode)'),
            ('Left-click on plot background', 'Place vertical guide'),
            ('Right-click on plot background', 'Clear vertical guide'),
        ])
        key_list = []
        val_list = []
        for key, value in help_text.items():
            key_label = widgets.Label(value=key)
            val_label = widgets.Label(value=value)

            key_list.append(key_label)
            val_list.append(val_label)

        self.instr_list.append(widgets.VBox(children=key_list))
        self.instr_list.append(widgets.VBox(children=val_list))

    # ====================================== DIMENSIONS SELECTION ======================================================
    def create_state_var_selection(self):
        no_state_vars = self.data.shape[1]
        state_vars = [i for i in range(no_state_vars)]
        self.state_var_radio_btn = widgets.RadioButtons(options=state_vars, layout={'width': 'max-content'})
        self.state_var_radio_btn.observe(self.state_var_update, names=['value'])

    def create_mode_selection(self):
        no_modes = self.data.shape[3]
        modes = [i for i in range(no_modes)]
        self.mode_radio_btn = widgets.RadioButtons(options=modes, layout={'width': 'max-content'})
        self.mode_radio_btn.observe(self.mode_update, names=['value'])

    def mode_update(self, s):
        selected = self.mode_radio_btn.value
        self.selected_mode = selected
        self.dimensions_selection_update()

    def state_var_update(self, s):
        selected = self.state_var_radio_btn.value
        self.selected_state_var = selected
        self.dimensions_selection_update()

    def dimensions_selection_update(self):
        self.configure_ts_widget()
        self.fig = self.raw.plot(duration=self.displayed_period, n_channels=self.no_channels, clipping=None,
                                 show=False)
        self.fig.set_size_inches(11, 7)

        with self.output:
            self.output.clear_output(wait=True)
            display(self.fig.canvas)

        # refresh the checkboxes if they were unselected
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
                if not cb.value:
                    cb.value = True

        # create the plot
        self.fig = self.raw.plot(duration=self.displayed_period, n_channels=self.no_channels, clipping=None, show=False)
        self.fig.mne.ch_order = self.ch_order
        self.fig.mne.ch_types = np.array(self.ch_types)

        # add custom widget handling on keyboard and mouse events
        self.fig.canvas.mpl_connect('key_press_event', update_on_plot_interaction)
        self.fig.canvas.mpl_connect('button_press_event', update_on_plot_interaction)

        # display the plot
        with plt.ioff():
            # create the plot
            self.fig = self.raw.plot(duration=self.displayed_period, n_channels=self.no_channels, clipping=None,
                                     show=False)
            self.fig.set_size_inches(11, 7)
            # self.fig.figure.canvas.set_window_title('TimeSeries plot')
            self.fig.mne.ch_order = self.ch_order
            self.fig.mne.ch_types = np.array(self.ch_types)

            # add custom widget handling on keyboard and mouse events
            self.fig.canvas.mpl_connect('key_press_event', update_on_plot_interaction)
            self.fig.canvas.mpl_connect('button_press_event', update_on_plot_interaction)

            with self.output:
                display(self.fig.canvas)

        items = [self.accordion, self.buttons_box, self.output]
        grid = widgets.GridBox(items)
        return grid

    # ======================================== CHECKBOXES ==============================================================
    def create_checkbox_list(self):
        checkboxes_stack = []
        labels = self.ch_names
        cb_per_col = math.ceil(len(labels) / 8)  # number of checkboxes in a column; should always display 8 cols
        for i, label in enumerate(labels):
            self.checkboxes[label] = widgets.Checkbox(value=True,
                                                      description=str(label),
                                                      disabled=False,
                                                      indent=False)
            self.checkboxes[label].observe(self.update_ts, names="value", type="change")
            if i and i % cb_per_col == 0:
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
            ch_number = ch_names.index(cb.description)  # get the number representation of checked/unchecked channel
            if cb.value:
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
        try:
            self.fig._redraw(annotations=True)
        except:
            self.fig._redraw(update_data=False)  # needed in case of Unselect all

# -*- coding: utf-8 -*-
#
# "TheVirtualBrain - Widgets" package
#
# (c) 2022-2023, TVB Widgets Team
#

import os
import math
import mne
import numpy as np
import ipywidgets as widgets
import matplotlib.pyplot as plt
from abc import ABC, abstractmethod
from IPython.core.display_functions import display
from tvb.datatypes.time_series import TimeSeries
from tvbwidgets.core.ini_parser import parse_ini_file
from tvbwidgets.core.exceptions import InvalidInputException
from tvbwidgets.ui.base_widget import TVBWidget


class ABCDataWrapper(ABC):
    """ Wrap any TimeSeries for TSWidget to read/parse uniformly"""
    extra_dimensions = {1: ("State var.", None),
                        3: ("Mode", None)}
    CHANNEL_TYPE = "misc"
    MAX_DISPLAYED_TIMEPOINTS = 3000

    @property
    def data_shape(self):
        # type: () -> tuple
        return ()

    @property
    def displayed_time_points(self):
        # type: () -> int
        return min(self.data_shape[0], self.MAX_DISPLAYED_TIMEPOINTS)

    @abstractmethod
    def get_channels_info(self):
        # type: () -> (list, list, list)
        pass

    @abstractmethod
    def get_ts_period(self):
        # type: () -> float
        pass

    @abstractmethod
    def get_ts_sample_rate(self):
        # type: () -> float
        pass

    @abstractmethod
    def build_raw(self, np_slice=None):
        # type: (tuple) -> mne.io.RawArray
        pass

    @abstractmethod
    def get_update_slice(self, sel1, sel2):
        # type: (int, int) -> tuple
        pass

    @abstractmethod
    def get_slice_for_time_point(self, time_point, channel, sel1=0, sel2=0):
        # type: (int, int, int, int) -> tuple
        pass

    @abstractmethod
    def get_hover_channel_value(self, x, ch_index, sel1, sel2):
        # type: (float, int, int, int) -> float
        pass


class WrapperTVB(ABCDataWrapper):
    """ Wrap TVB TimeSeries object for tsWidget"""

    def __init__(self, data):
        # type: (TimeSeries) -> None
        if data is None or not isinstance(data, TimeSeries):
            raise InvalidInputException("Not a valid TVB TS " + str(data))
        self.data = data
        self.ch_names = []
        variables_labels = data.variables_labels
        if variables_labels is not None and variables_labels != []:
            sv_options = [(variables_labels[idx], idx) for idx in range(len(variables_labels))]
            self.extra_dimensions = ABCDataWrapper.extra_dimensions.copy()
            self.extra_dimensions[1] = ("State var.", sv_options)

    @property
    def data_shape(self):
        # type: () -> tuple
        return self.data.shape

    def get_channels_info(self):
        # type: () -> (list, list, list)
        no_channels = self.data.shape[2]  # number of channels is on axis 2

        if hasattr(self.data, "connectivity"):
            ch_names = self.data.connectivity.region_labels.tolist()
        elif hasattr(self.data, "sensors"):
            ch_names = self.data.sensors.labels.tolist()
        else:
            ch_names = ['signal-%d' % i for i in range(no_channels)]

        ch_order = list(range(no_channels))  # the order should be the order in which they are provided
        ch_types = [self.CHANNEL_TYPE for _ in ch_names]
        self.ch_names = ch_names
        return ch_names, ch_order, ch_types

    def get_ts_period(self):
        # type: () -> float
        displayed_period = self.data.sample_period * self.displayed_time_points
        return displayed_period

    def get_ts_sample_rate(self):
        # type: () -> float
        return self.data.sample_rate

    def build_raw(self, np_slice=None):
        # type: (tuple) -> mne.io.RawArray
        if np_slice is None:
            np_slice = self.get_update_slice()
        raw_info = mne.create_info(self.ch_names, sfreq=self.data.sample_rate)
        data_for_raw = self.data.data[np_slice].squeeze()
        data_for_raw = np.swapaxes(data_for_raw, 0, 1)
        raw = mne.io.RawArray(data_for_raw, raw_info, first_samp=self.data.start_time * self.data.sample_rate)
        return raw

    def get_update_slice(self, sel1=0, sel2=0):
        # type: (int, int) -> tuple
        new_slice = (slice(None), slice(sel1, sel1 + 1), slice(None), slice(sel2, sel2 + 1))
        return new_slice

    def get_slice_for_time_point(self, time_point, channel, sel1=0, sel2=0):
        # type: (int, int, int, int) -> tuple
        new_slice = (slice(time_point, time_point + 1), slice(sel1, sel1 + 1),
                     slice(channel, channel + 1), slice(sel2, sel2 + 1))
        return new_slice

    def get_hover_channel_value(self, x, ch_index, sel1, sel2):
        # type: (float, int, int, int) -> float
        time_per_tp = self.get_ts_period() / self.displayed_time_points  # time unit displayed in 1 time point

        # which time point to search in the time points array
        tp_on_hover = round((x - self.data.start_time) / time_per_tp)
        new_slice = self.get_slice_for_time_point(tp_on_hover, ch_index, sel1, sel2)

        ch_value = self.data.data[new_slice].squeeze().item(0)
        ch_value = round(ch_value, 4)

        return ch_value


class WrapperNumpy(ABCDataWrapper):
    """ Wrap a numpy array for tsWidget """

    def __init__(self, data, sample_rate, channel_names=None, ch_idx=2):
        # type: (np.ndarray, float, list, int) -> None
        """
        :param data: Numpy array 2D up to 4D
        :param sample_rate: float
        :param channel_names: optional names for channels
        :param ch_idx: Channels Index from the max 4D of the data. We assume time is on 0
        """
        if data is None or not isinstance(data, np.ndarray) or len(data.shape) <= 1:
            raise InvalidInputException("Not a valid numpy array %s \n "
                                        "It should be numpy.ndarray, at least 2D up to 4D" % str(data))
        self.data = data
        self.sample_rate = sample_rate
        self.ch_names = channel_names or []
        self.ch_idx = ch_idx

    @property
    def data_shape(self):
        # type: () -> tuple
        return self.data.shape

    def get_channels_info(self):
        # type: () -> (list, list, list)
        no_channels = self.data.shape[self.ch_idx]
        if (self.ch_names is None) or len(self.ch_names) != no_channels:
            self.ch_names = ['signal-%d' % i for i in range(no_channels)]
        ch_order = list(range(no_channels))  # the order should be the order in which they are provided
        ch_types = [self.CHANNEL_TYPE for _ in self.ch_names]
        return self.ch_names, ch_order, ch_types

    def get_ts_period(self):
        # type: () -> float
        sample_period = 1 / self.sample_rate
        displayed_period = sample_period * self.displayed_time_points
        return displayed_period

    def get_ts_sample_rate(self):
        # type: () -> float
        return self.sample_rate

    def build_raw(self, np_slice=None):
        # type: (tuple) -> mne.io.RawArray
        if np_slice is None:
            np_slice = self.get_update_slice()
        raw_info = mne.create_info(self.ch_names, sfreq=self.sample_rate)
        data_for_raw = self.data[np_slice]
        data_for_raw = data_for_raw.squeeze()
        data_for_raw = np.swapaxes(data_for_raw, 0, 1)
        raw = mne.io.RawArray(data_for_raw, raw_info)
        return raw

    def get_update_slice(self, sel1=0, sel2=0):
        # type: (int, int) -> tuple
        sel2 = sel2 if sel2 is not None else 0
        no_dim = len(self.data_shape)
        dim_to_slice_dict = {
            2: (slice(None), slice(None)),
            3: (slice(None), slice(sel1, sel1 + 1), slice(None)),
            4: (slice(None), slice(sel1, sel1 + 1), slice(None), slice(sel2, sel2 + 1))
        }
        new_slice = dim_to_slice_dict[no_dim]
        return new_slice

    def get_slice_for_time_point(self, time_point, channel, sel1=0, sel2=0):
        # type: (int, int, int, int) -> tuple
        sel1 = sel1 if sel1 is not None else 0
        sel2 = sel2 if sel2 is not None else 0
        no_dim = len(self.data_shape)
        dim_to_slice_dict = {
            2: (slice(time_point, time_point + 1), slice(channel, channel + 1)),
            3: (slice(time_point, time_point + 1), slice(sel1, sel1 + 1), slice(channel, channel + 1)),
            4: (slice(time_point, time_point + 1), slice(sel1, sel1 + 1),
                slice(channel, channel + 1), slice(sel2, sel2 + 1))
        }
        new_slice = dim_to_slice_dict[no_dim]
        return new_slice

    def get_hover_channel_value(self, x, ch_index, sel1, sel2):
        # type: (float, int, int, int) -> float
        time_per_tp = self.get_ts_period() / self.displayed_time_points  # time unit displayed in 1 time point

        # which time point to search in the time points array
        tp_on_hover = round(x / time_per_tp)
        new_slice = self.get_slice_for_time_point(tp_on_hover, ch_index, sel1, sel2)

        ch_value = self.data[new_slice].squeeze().item(0)
        ch_value = round(ch_value, 4)

        return ch_value


class TimeSeriesWidget(widgets.VBox, TVBWidget):
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

        self.output = widgets.Output(layout=widgets.Layout(width='auto'))
        annotation_area = self._create_annotation_area()
        instr_area = self._create_instructions_region()
        self.title_area = widgets.HBox(children=[instr_area])

        self.checkboxes = dict()
        super().__init__([self.output, annotation_area, self.title_area], layout=self.DEFAULT_BORDER)
        self.logger.info("TimeSeries Widget initialized")

    def add_datatype(self, ts_tvb):
        # type: (TimeSeries) -> None
        data_wrapper = WrapperTVB(ts_tvb)
        self.logger.debug("Adding TVB TS for display...")
        self._populate_from_data_wrapper(data_wrapper)

    def _populate_from_data_wrapper(self, data_wrapper):
        # type: (ABCDataWrapper) -> None
        if self.data is not None:
            raise InvalidInputException("TSWidget is not yet capable to display more than one TS!")

        self.data = data_wrapper
        self.sample_freq = data_wrapper.get_ts_sample_rate()
        self.displayed_period = data_wrapper.get_ts_period()
        self.ch_names, self.ch_order, self.ch_types = data_wrapper.get_channels_info()
        self.raw = self.data.build_raw()
        channels_area = self._create_checkboxes(data_wrapper)
        self.title_area.children += (channels_area,)
        self._redraw()

    def add_data_array(self, numpy_array, sample_freq, ch_idx):
        # type: (np.array, float, int) -> None
        data_wrapper = WrapperNumpy(numpy_array, sample_freq, ch_idx=ch_idx)
        self._populate_from_data_wrapper(data_wrapper)

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
    def _redraw(self):
        def update_on_plot_interaction(_):
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

        def hover(event):
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

        # display the plot
        with plt.ioff():
            # create the plot
            self.fig = self.raw.plot(duration=self.displayed_period,
                                     n_channels=self.no_channels, show_first_samp=True,
                                     clipping=None, show=False)
            self.fig.set_size_inches(11, 5)
            # self.fig.figure.canvas.set_window_title('TimeSeries plot')
            self.fig.mne.ch_order = self.ch_order
            self.fig.mne.ch_types = np.array(self.ch_types)

            # add custom widget handling on keyboard and mouse events
            self.fig.canvas.mpl_connect('key_press_event', update_on_plot_interaction)
            self.fig.canvas.mpl_connect('button_press_event', update_on_plot_interaction)
            self.fig.canvas.mpl_connect("motion_notify_event", hover)

            with self.output:
                display(self.fig.canvas)

    # ======================================== CHANNELS  ==============================================================
    def _unselect_all(self, _):
        self.logger.debug("Unselect all was called!")
        for cb_name in self.checkboxes:
            self.checkboxes[cb_name].value = False

    def _select_all(self, _):
        self.logger.debug("Select all was called!")
        for cb_name in self.checkboxes:
            self.checkboxes[cb_name].value = True

    def _create_checkboxes(self, array_wrapper):
        # type: (ABCDataWrapper) -> widgets.Accordion
        checkboxes_list, checkboxes_stack = [], []
        labels = array_wrapper.get_channels_info()[0]
        cb_per_col = math.ceil(len(labels) / 7)  # number of checkboxes in a column; should always display 7 cols
        for i, label in enumerate(labels):
            self.checkboxes[label] = widgets.Checkbox(value=True, description=label,
                                                      disabled=False, indent=False)
            self.checkboxes[label].observe(self._update_ts, names="value", type="change")
            if i and i % cb_per_col == 0:
                checkboxes_list.append(widgets.VBox(children=checkboxes_stack))
                checkboxes_stack = []
            checkboxes_stack.append(self.checkboxes[label])
        checkboxes_list.append(widgets.VBox(children=checkboxes_stack))
        checkboxes_region = widgets.HBox(children=checkboxes_list, layout={'width': '540px',
                                                                           'height': 'max-content'})

        # buttons region
        select_all_btn = widgets.Button(description="Select all", layout=self.BUTTON_STYLE)
        select_all_btn.on_click(self._select_all)
        unselect_all_btn = widgets.Button(description="Unselect all", layout=self.BUTTON_STYLE)
        unselect_all_btn.on_click(self._unselect_all)
        actions = [select_all_btn, unselect_all_btn]

        # select dimensions region
        self.radio_buttons = []
        for idx, info in array_wrapper.extra_dimensions.items():
            extra_area, extra_radio_btn = self._create_selection(info[0], idx, dim_options=info[1])
            self.radio_buttons.append(extra_radio_btn)
            if extra_area is not None:
                actions.append(extra_area)

        channels_region = widgets.VBox(children=[widgets.HBox(actions), checkboxes_region])
        channels_area = widgets.Accordion(children=[channels_region], selected_index=None,
                                          layout=widgets.Layout(width='50%'))
        channels_area.set_title(0, 'Channels')
        return channels_area

    def _create_selection(self, title="Mode", shape_pos=3, dim_options=None):

        if self.data is None or len(self.data.data_shape) <= max(2, shape_pos):
            return None, None

        no_dims = self.data.data_shape[shape_pos]
        if dim_options is None or dim_options == []:
            dim_options = [i for i in range(no_dims)]
        sel_radio_btn = widgets.RadioButtons(options=dim_options, layout={'width': 'max-content'})
        sel_radio_btn.observe(self._dimensions_selection_update, names=['value'])
        accordion = widgets.Accordion(children=[sel_radio_btn], selected_index=None, layout={'width': '30%'})
        accordion.set_title(0, title)
        return accordion, sel_radio_btn

    def _get_selection_values(self):
        sel1 = self.radio_buttons[0].value if self.radio_buttons[0] else None
        sel2 = self.radio_buttons[1].value if self.radio_buttons[1] else None
        return sel1, sel2

    def _dimensions_selection_update(self, _):
        # update self.raw and linked parts
        sel1, sel2 = self._get_selection_values()
        new_slice = self.data.get_update_slice(sel1, sel2)
        self.logger.info("New slice " + str(new_slice))
        self.raw = self.data.build_raw(new_slice)
        self.fig = self.raw.plot(duration=self.displayed_period,
                                 n_channels=self.no_channels,
                                 clipping=None, show=False)
        self.fig.set_size_inches(11, 5)

        with self.output:
            self.output.clear_output(wait=True)
            display(self.fig.canvas)

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
        for cb in list(self.checkboxes.values()):
            ch_number = ch_names.index(cb.description)  # get the number representation of checked/unchecked channel
            if cb.value:
                picks.append(ch_number)  # list with number representation of channels
            else:
                not_picked.append(ch_number)

        # for unselect all
        if not picks:
            self.fig.mne.picks = picks
            self.fig.mne.n_channels = 0
            self._update_fig()
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

    def _update_fig(self):
        self.fig._update_trace_offsets()
        self.fig._update_vscroll()
        try:
            self.fig._redraw(annotations=True)
        except:
            self.fig._redraw(update_data=False)  # needed in case of Unselect all

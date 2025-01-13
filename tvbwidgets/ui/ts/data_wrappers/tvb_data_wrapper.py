# -*- coding: utf-8 -*-
#
# "TheVirtualBrain - Widgets" package
#
# (c) 2022-2025, TVB Widgets Team
#

import mne
import numpy as np
from tvb.datatypes.time_series import TimeSeries
from tvbwidgets.core.exceptions import InvalidInputException
from tvbwidgets.ui.ts.data_wrappers.base_data_wrapper import ABCDataWrapper


class WrapperTVB(ABCDataWrapper):
    """ Wrap TVB TimeSeries object for tsWidget"""

    def __init__(self, data):
        # type: (TimeSeries) -> None
        if data is None or not isinstance(data, TimeSeries):
            raise InvalidInputException("Not a valid TVB TS " + str(data))
        self.data = data
        self.ch_names = []
        variables_labels = data.variables_labels    # this give a numpy.ndarray
        if variables_labels is not None and variables_labels.size != 0:
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

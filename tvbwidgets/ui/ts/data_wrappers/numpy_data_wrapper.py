# -*- coding: utf-8 -*-
#
# "TheVirtualBrain - Widgets" package
#
# (c) 2022-2025, TVB Widgets Team
#

import mne
import numpy as np
from tvbwidgets.core.exceptions import InvalidInputException
from tvbwidgets.ui.ts.data_wrappers.base_data_wrapper import ABCDataWrapper


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

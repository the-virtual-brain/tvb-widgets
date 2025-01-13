# -*- coding: utf-8 -*-
#
# "TheVirtualBrain - Widgets" package
#
# (c) 2022-2025, TVB Widgets Team
#

from abc import ABC, abstractmethod


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

# -*- coding: utf-8 -*-
#
# "TheVirtualBrain - Widgets" package
#
# (c) 2022-2025, TVB Widgets Team
#

import mne
import numpy as np


def read_edf_file(filepath):
    # type: (str) -> (numpy.ndarray, float, int)
    """
    Reads an EDF file located at filepath and returns the data array, the sample frequency and the channel index,
    all necessary for the `api.plot_timeseries` function
    """
    raw = mne.io.read_raw_edf(filepath)
    data, _ = raw[:]
    data = np.transpose(data)
    ch_idx = len(data.shape) - 1
    sample_freq = raw.info['sfreq']

    return data, sample_freq, ch_idx
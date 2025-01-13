# -*- coding: utf-8 -*-
#
# "TheVirtualBrain - Widgets" package
#
# (c) 2022-2025, TVB Widgets Team
#

import math
import numpy as np
import pytest

from tvbwidgets.tests.ts.ts_generator import generate_ts_with_mode_and_sv
from tvbwidgets.ui.ts.data_wrappers.numpy_data_wrapper import WrapperNumpy
from tvbwidgets.ui.ts.data_wrappers.tvb_data_wrapper import WrapperTVB


# =========================================== TEST WRAPPER NUMPY =======================================================
@pytest.fixture
def wrapper_np():
    """ Returns an initialized Numpy wrapper with 3 dimensions """
    rng = np.random.default_rng(50)
    numpy_array = rng.random(size=(30000, 4, 50))
    wrapper_np = WrapperNumpy(numpy_array, 0.01, ch_idx=2)
    return wrapper_np


def test_data_shape_np(wrapper_np):
    assert wrapper_np.data_shape == (30000, 4, 50)


def test_get_channel_info_np(wrapper_np):
    ch_names, ch_order, ch_type = wrapper_np.get_channels_info()
    assert ch_names == [f'signal-{x}' for x in range(50)]
    assert len(ch_names) == len(ch_order) == len(ch_type) == 50


def test_get_ts_period_np(wrapper_np):
    assert wrapper_np.get_ts_period() == 300000


def test_get_sample_rate_np(wrapper_np):
    assert math.isclose(wrapper_np.get_ts_sample_rate(), 0.01)


def test_build_raw_np(wrapper_np):
    wrapper_np.get_channels_info()  # need to init ch_names for wrapper

    raw = wrapper_np.build_raw()
    data = wrapper_np.data[:, 0, :].squeeze()
    data = np.swapaxes(data, 0, 1)

    assert np.array_equal(raw.get_data(), data)


def test_get_update_slice_np(wrapper_np):
    sel1 = 1
    new_slice = wrapper_np.get_update_slice(sel1)
    data_with_slice = wrapper_np.data[new_slice].squeeze()
    new_data = wrapper_np.data[:, sel1, :]
    assert np.array_equal(data_with_slice, new_data)


def test_get_hover_channel_value_np(wrapper_np):
    time_per_tp = 100
    x = 2999900
    x_int = round(x / time_per_tp)
    ch_index = 0
    sel1 = 0

    ch_value = wrapper_np.get_hover_channel_value(x, ch_index, sel1, None)
    val = wrapper_np.data[x_int, sel1, ch_index]
    val = round(val, 4)

    assert ch_value == val


# ============================================ TEST WRAPPER TVB ========================================================
@pytest.fixture(scope="module")
def tsr_4d():
    """ Returns a TVB TS having SV and Mode """
    return generate_ts_with_mode_and_sv(length=1e3, cutoff=100)


@pytest.fixture
def wrapper_tvb(tsr_4d):
    """ Returns an initialized WrapperTVB """
    return WrapperTVB(tsr_4d)


def test_build_wrapper_tvb(wrapper_tvb):
    assert wrapper_tvb.data_shape == (4000, 4, 76, 1)

    ch_names, ch_order, ch_type = wrapper_tvb.get_channels_info()
    assert len(ch_names) == len(ch_order) == len(ch_type) == 76

    assert wrapper_tvb.displayed_time_points == 3000
    assert math.isclose(wrapper_tvb.get_ts_period(), 0.75)
    assert wrapper_tvb.get_ts_sample_rate() == 4000

    raw = wrapper_tvb.build_raw()
    data = wrapper_tvb.data.data[:, 0, :, 0].squeeze()
    data = np.swapaxes(data, 0, 1)

    assert np.array_equal(raw.get_data(), data)


def test_get_channels_info_tvb(wrapper_tvb):
    ch_names, ch_order, ch_type = wrapper_tvb.get_channels_info()
    assert ch_names == [f'sig {x}' for x in range(76)]
    assert len(ch_names) == len(ch_order) == len(ch_type) == 76


def test_get_update_slice_tvb(wrapper_tvb):
    sel1 = 2
    sel2 = 0
    new_slice = wrapper_tvb.get_update_slice(sel1, sel2)
    data_with_slice = wrapper_tvb.data.data[new_slice].squeeze()
    new_data = wrapper_tvb.data.data[:, sel1, :, sel2]

    assert np.array_equal(data_with_slice, new_data)


def test_get_ts_period_tvb(wrapper_tvb):
    ts_period = wrapper_tvb.get_ts_period()
    assert math.isclose(ts_period, 0.75)


def test_get_ts_sample_rate_tvb(wrapper_tvb):
    sample_rate = wrapper_tvb.get_ts_sample_rate()
    assert sample_rate == 4000


def test_build_raw_tvb(wrapper_tvb):
    wrapper_tvb.get_channels_info()  # need to init ch_names for wrapper

    raw = wrapper_tvb.build_raw()
    data = wrapper_tvb.data.data[:, 0, :, :].squeeze()
    data = np.swapaxes(data, 0, 1)

    assert np.array_equal(raw.get_data(), data)


def test_get_update_slice_tvb(wrapper_tvb):
    sel1 = 1  # for sel2 use default value
    new_slice = wrapper_tvb.get_update_slice(sel1)
    data_with_slice = wrapper_tvb.data.data[new_slice].squeeze()
    new_data = wrapper_tvb.data.data[:, sel1, :, 0]
    assert np.array_equal(data_with_slice, new_data)


def test_get_slice_for_time_point_tvb(wrapper_tvb):
    sel1 = 1  # for sel2 use default value
    tp = 1500
    ch = 16
    new_slice = wrapper_tvb.get_slice_for_time_point(time_point=tp, channel=ch, sel1=sel1)
    data_with_slice = wrapper_tvb.data.data[new_slice].squeeze()
    new_data = wrapper_tvb.data.data[tp, sel1, ch, 0]
    assert np.array_equal(data_with_slice, new_data)


def test_get_hover_channel_value_tvb(wrapper_tvb):
    start_time = 0.100125
    time_per_tp = 0.00025

    x = 1.099
    x_int = round((x - start_time) / time_per_tp)
    ch_index = 6
    sel1 = 0
    sel2 = 0

    ch_value = wrapper_tvb.get_hover_channel_value(x, ch_index, sel1, sel2)
    val = wrapper_tvb.data.data[x_int, sel1, ch_index, sel2]
    val = round(val, 4)
    assert ch_value == val



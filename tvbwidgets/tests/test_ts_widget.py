# -*- coding: utf-8 -*-
#
# "TheVirtualBrain - Widgets" package
#
# (c) 2022-2023, TVB Widgets Team
#

import pytest
import logging
import numpy as np
from ipywidgets import Checkbox
from tvbwidgets.tests.ts_generator import generate_ts_with_mode_and_sv
from tvbwidgets.ui.ts_widget import TimeSeriesWidget, WrapperTVB, WrapperNumpy


# =========================================== TEST WRAPPER NUMPY =======================================================
@pytest.fixture
def wrapper_np():
    """ Returns an initialized Numpy wrapper with 3 dimensions """
    numpy_array = np.random.rand(30000, 4, 50)
    wrapper_np = WrapperNumpy(numpy_array, 0.01, ch_idx=2)
    return wrapper_np


def test_data_shape_wrapper_np(wrapper_np):
    assert wrapper_np.data_shape == (30000, 4, 50)


def test_get_channel_info_wrapper_np(wrapper_np):
    ch_names, ch_order, ch_type = wrapper_np.get_channels_info()
    assert len(ch_names) == len(ch_order) == len(ch_type) == 50


def test_get_ts_period_wrapper_np(wrapper_np):
    assert wrapper_np.get_ts_period() == 300000


def test_get_sample_rate_wrapper_np(wrapper_np):
    assert wrapper_np.get_ts_sample_rate() == 0.01


def test_build_raw_wrapper_np(wrapper_np):
    wrapper_np.get_channels_info()  # need to init ch_names for wrapper

    raw = wrapper_np.build_raw()
    data = wrapper_np.data[:, 0, :].squeeze()
    data = np.swapaxes(data, 0, 1)

    assert np.array_equal(raw.get_data(), data)


def test_get_update_slice_wrapper_np(wrapper_np):
    sel1 = 1
    new_slice = wrapper_np.get_update_slice(sel1)
    data_with_slice = wrapper_np.data[new_slice].squeeze()
    new_data = wrapper_np.data[:, sel1, :]
    assert np.array_equal(data_with_slice, new_data)


def test_get_hover_channel_value_wrapper_np(wrapper_np):
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
    assert wrapper_tvb.get_ts_period() == 0.75
    assert wrapper_tvb.get_ts_sample_rate() == 4000

    raw = wrapper_tvb.build_raw()
    data = wrapper_tvb.data.data[:, 0, :, 0].squeeze()
    data = np.swapaxes(data, 0, 1)

    assert np.array_equal(raw.get_data(), data)


def test_get_update_slice_wrapper_tvb(wrapper_tvb):
    sel1 = 2
    sel2 = 0
    new_slice = wrapper_tvb.get_update_slice(sel1, sel2)
    data_with_slice = wrapper_tvb.data.data[new_slice].squeeze()
    new_data = wrapper_tvb.data.data[:, sel1, :, sel2]

    assert np.array_equal(data_with_slice, new_data)


def test_get_hover_channel_value_wrapper_tvb(wrapper_tvb):
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


# ============================================= TEST TS WIDGET =========================================================
@pytest.fixture
def tsw():
    """ Returns an empty TS widget """
    return TimeSeriesWidget()


@pytest.fixture
def tsw_tvb_data(tsr_4d):
    """ Returns a TS widget initialized with a tvb data wrapper"""
    tsw_tvb_data = TimeSeriesWidget()
    tsw_tvb_data.add_datatype(tsr_4d)
    return tsw_tvb_data


def test_create_ts_widget(tsw):
    assert tsw.ch_names == []
    assert tsw.ch_order == []
    assert tsw.ch_types == []
    assert tsw.displayed_period == 0
    assert tsw.no_channels == 30
    assert tsw.sample_freq == 0


def test_populate_from_data_wrapper_tvb(tsw, wrapper_tvb):
    tsw._populate_from_data_wrapper(wrapper_tvb)

    assert tsw.data == wrapper_tvb
    assert tsw.sample_freq == 4000
    assert tsw.displayed_period == 0.75
    assert len(tsw.ch_names) == len(tsw.ch_order) == len(tsw.ch_types) == 76
    assert tsw.raw.get_data().shape == (76, 4000)


def test_create_selection(tsw_tvb_data):
    title = "State variable"
    pos = 1
    accordion, radio_button = tsw_tvb_data._create_selection(title=title, shape_pos=pos)
    assert radio_button.options == (0, 1, 2, 3)
    assert accordion.get_title(0) == title


def test_create_checkboxes(tsw_tvb_data):
    tsw_tvb_data.data.get_channels_info()  # need to initialize ch_names for wrapper
    channels_area = tsw_tvb_data._create_checkboxes(tsw_tvb_data.data)
    assert len(tsw_tvb_data.checkboxes) == 76
    assert len(tsw_tvb_data.radio_buttons) == 2
    assert channels_area.get_title(0) == 'Channels'


def test_get_widget(tsw_tvb_data):
    tsw_tvb_data.get_widget()
    assert type(tsw_tvb_data) == TimeSeriesWidget


def test_update_ts(caplog, tsw_tvb_data):
    logger = logging.getLogger('tvbwidgets')
    logger.propagate = True
    val = {'name': 'value', 'old': True, 'new': False,
           'owner': Checkbox(value=False, description='signal-0', indent=False), 'type': 'change'}

    caplog.clear()
    tsw_tvb_data.get_widget()
    tsw_tvb_data._update_ts(val)
    assert caplog.records[0].levelname == 'DEBUG'
    assert 'Update_ts' in caplog.text


def test_create_instructions_region():
    instr_area = TimeSeriesWidget._create_instructions_region()

    shortcuts = instr_area.children[0].children[0].children
    descriptions = instr_area.children[0].children[1].children

    no_instruction = 27
    assert len(shortcuts) == len(descriptions) == no_instruction

    title = 'Keyboard shortcuts'
    assert instr_area.get_title(0) == title


def test_get_next_checked_channel():
    ch_start = 0
    checked_list = [2, 3, 4, 5]
    ch_order = [0, 1, 2, 3, 4, 5]
    assert TimeSeriesWidget._get_next_checked_channel(ch_start, checked_list, ch_order) == 2

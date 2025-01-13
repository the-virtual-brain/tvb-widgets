# -*- coding: utf-8 -*-
#
# "TheVirtualBrain - Widgets" package
#
# (c) 2022-2025, TVB Widgets Team
#

import math
import numpy as np
import pytest
import logging
from ipywidgets import Checkbox
from tvbwidgets.tests.ts.ts_generator import generate_ts_with_mode_and_sv
from tvbwidgets.ui.ts.data_wrappers.tvb_data_wrapper import WrapperTVB
from tvbwidgets.ui.ts.mne_ts_widget import TimeSeriesWidgetMNE


@pytest.fixture(scope="module")
def tsr_4d():
    """ Returns a TVB TS having SV and Mode """
    return generate_ts_with_mode_and_sv(length=1e3, cutoff=100)


@pytest.fixture
def wrapper_tvb(tsr_4d):
    """ Returns an initialized WrapperTVB """
    return WrapperTVB(tsr_4d)


@pytest.fixture
def tsw():
    """ Returns an empty TSWidgetMNE """
    return TimeSeriesWidgetMNE()


@pytest.fixture
def tsw_tvb_data(tsr_4d):
    """ Returns a TS widget initialized with a tvb data wrapper"""
    tsw_tvb_data = TimeSeriesWidgetMNE()
    tsw_tvb_data.add_datatype(tsr_4d)
    return tsw_tvb_data


# =========================================== WIDGET CREATION ==========================================================
def test_get_widget(tsw_tvb_data):
    tsw_tvb_data.get_widget()
    assert isinstance(tsw_tvb_data, TimeSeriesWidgetMNE)


def test_create_ts_widget(tsw):
    assert tsw.ch_names == []
    assert tsw.ch_order == []
    assert tsw.ch_types == []
    assert tsw.displayed_period == 0
    assert tsw.no_channels == 30
    assert tsw.sample_freq == 0


# =============================================== SETUP ================================================================
def test_reset_data(tsw, tsr_4d):
    tsw.add_data(tsr_4d)
    tsw.reset_data()
    assert tsw.data is None


def test_populate_from_data_wrapper_tvb(tsw, wrapper_tvb):
    tsw._populate_from_data_wrapper(wrapper_tvb)

    assert tsw.data == wrapper_tvb
    assert tsw.sample_freq == 4000
    assert math.isclose(tsw.displayed_period, 0.75)
    assert len(tsw.ch_names) == len(tsw.ch_order) == len(tsw.ch_types) == 76
    assert tsw.raw.get_data().shape == (76, 4000)


# ======================================== CHANNEL VALUE AREA ======================================================
def test_create_annotation_area(tsw_tvb_data):
    ann_area = tsw_tvb_data._create_annotation_area()
    assert len(ann_area.children) == 2
    assert ann_area.children[0].value == 'Channel values:'


# ===================================== INSTRUCTIONS DROPDOWN ======================================================
def test_create_instructions_region():
    instr_area = TimeSeriesWidgetMNE._create_instructions_region()

    shortcuts = instr_area.children[0].children[0].children
    descriptions = instr_area.children[0].children[1].children

    no_instruction = 22
    assert len(shortcuts) == len(descriptions) == no_instruction

    title = 'Keyboard shortcuts'
    assert instr_area.get_title(0) == title


# ======================================== CHANNELS  ==============================================================
def test_create_channel_selection_area(tsw_tvb_data):
    tsw_tvb_data.data.get_channels_info()  # need to initialize ch_names for wrapper
    channels_area = tsw_tvb_data._create_channel_selection_area(tsw_tvb_data.data)
    assert len(tsw_tvb_data.checkboxes) == 76
    assert len(tsw_tvb_data.radio_buttons) == 2
    assert channels_area.get_title(0) == 'Channels'


def test_dimensions_selection_update(tsw_tvb_data):
    # simulate unchecking of some checkboxes
    rng = np.random.default_rng(50)
    false_cb_idx = list(rng.choice(76, size=3, replace=False))
    false_cb_names = [f'sig {x}' for x in false_cb_idx]
    for cb_name in false_cb_names:
        tsw_tvb_data.checkboxes[cb_name].value = False

    no_false_cb = len([x for x in tsw_tvb_data.checkboxes if tsw_tvb_data.checkboxes[x].value == False])
    assert no_false_cb == 3

    # after selection update, make sure all channel checkboxes are checked
    tsw_tvb_data._dimensions_selection_update(True)
    for cb_name in tsw_tvb_data.checkboxes:
        assert tsw_tvb_data.checkboxes[cb_name].value == True


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


def test_get_next_checked_channel():
    ch_start = 0
    checked_list = [2, 3, 4, 5]
    ch_order = [0, 1, 2, 3, 4, 5]
    assert TimeSeriesWidgetMNE._get_next_checked_channel(ch_start, checked_list, ch_order) == 2

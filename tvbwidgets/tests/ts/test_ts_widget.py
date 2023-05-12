# -*- coding: utf-8 -*-
#
# "TheVirtualBrain - Widgets" package
#
# (c) 2022-2023, TVB Widgets Team
#

import pytest
import logging
from ipywidgets import Checkbox
from tvbwidgets.ui.ts.mne_ts_widget import TimeSeriesWidgetMNE


# ============================================= TEST TS WIDGET =========================================================
@pytest.fixture
def tsw():
    """ Returns an empty TS widget """
    return TimeSeriesWidgetMNE()


@pytest.fixture
def tsw_tvb_data(tsr_4d):
    """ Returns a TS widget initialized with a tvb data wrapper"""
    tsw_tvb_data = TimeSeriesWidgetMNE()
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
    channels_area = tsw_tvb_data._create_channel_selection_area(tsw_tvb_data.data)
    assert len(tsw_tvb_data.checkboxes) == 76
    assert len(tsw_tvb_data.radio_buttons) == 2
    assert channels_area.get_title(0) == 'Channels'


def test_get_widget(tsw_tvb_data):
    tsw_tvb_data.get_widget()
    assert type(tsw_tvb_data) == TimeSeriesWidgetMNE


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
    instr_area = TimeSeriesWidgetMNE._create_instructions_region()

    shortcuts = instr_area.children[0].children[0].children
    descriptions = instr_area.children[0].children[1].children

    no_instruction = 23
    assert len(shortcuts) == len(descriptions) == no_instruction

    title = 'Keyboard shortcuts'
    assert instr_area.get_title(0) == title


def test_get_next_checked_channel():
    ch_start = 0
    checked_list = [2, 3, 4, 5]
    ch_order = [0, 1, 2, 3, 4, 5]
    assert TimeSeriesWidgetMNE._get_next_checked_channel(ch_start, checked_list, ch_order) == 2

# -*- coding: utf-8 -*-
#
# "TheVirtualBrain - Widgets" package
#
# (c) 2022-2025, TVB Widgets Team
#

import math
import pytest

import ipywidgets as widgets
from plotly_resampler import FigureWidgetResampler

from tvbwidgets.tests.ts.ts_generator import generate_ts_with_mode_and_sv
from tvbwidgets.ui.ts.data_wrappers.tvb_data_wrapper import WrapperTVB
from tvbwidgets.ui.ts.plotly_ts_widget import TimeSeriesWidgetPlotly


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
    return TimeSeriesWidgetPlotly()


@pytest.fixture
def tsw_tvb_data(tsr_4d):
    """ Returns a TS widget initialized with a tvb data wrapper"""
    tsw_tvb_data = TimeSeriesWidgetPlotly()
    tsw_tvb_data.add_datatype(tsr_4d)
    return tsw_tvb_data


# =========================================== WIDGET CREATION ==========================================================
def test_get_widget(tsw_tvb_data):
    tsw_tvb_data.get_widget()
    assert isinstance(tsw_tvb_data, TimeSeriesWidgetPlotly)


def test_create_ts_widget(tsw):
    assert tsw.ch_names == []
    assert not hasattr(tsw, 'ch_order')
    assert not hasattr(tsw, 'ch_types')
    assert tsw.start_time == 0
    assert tsw.end_time == 0
    assert tsw.std_step == 0
    assert tsw.amplitude == 1
    assert len(tsw.children) == 3


# =============================================== SETUP ================================================================
def test_populate_from_data_wrapper_tvb(tsw, wrapper_tvb):
    tsw._populate_from_data_wrapper(wrapper_tvb)

    assert tsw.data == wrapper_tvb
    assert tsw.sample_freq == 4000
    assert math.isclose(tsw.displayed_period, 0.75)
    assert len(tsw.ch_names) == 76
    assert tsw.raw.get_data().shape == (76, 4000)


# ============================================== PLOT ==================================================================
def test_add_traces_to_plot(tsw_tvb_data):
    data = tsw_tvb_data.raw[:, :][0]
    ch_names = tsw_tvb_data.ch_names

    # reset widget figure to test add_traces (add_traces is automatically called during widget setup)
    tsw_tvb_data.fig = FigureWidgetResampler()
    tsw_tvb_data.add_traces_to_plot(data, ch_names)
    assert len(tsw_tvb_data.fig.data) == 76


def test_populate_plot(tsw_tvb_data):
    data = tsw_tvb_data.raw[:, :][0]
    ch_names = tsw_tvb_data.ch_names
    tsw_tvb_data.fig = None

    tsw_tvb_data.fig = FigureWidgetResampler()
    tsw_tvb_data._populate_plot(data, ch_names)
    assert len(tsw_tvb_data.fig.data) == 76
    assert len(tsw_tvb_data.fig.layout.annotations) == 76
    assert tsw_tvb_data.fig.layout.annotations[0]['text'] == 'sig 75'    # list is reversed


def test_add_visibility_buttons(tsw_tvb_data):
    tsw_tvb_data.fig = None

    tsw_tvb_data.fig = FigureWidgetResampler()
    tsw_tvb_data.add_visibility_buttons()
    assert len(tsw_tvb_data.fig.layout.updatemenus[0].buttons) == 2
    assert tsw_tvb_data.fig.layout.updatemenus[0].buttons[0].label == 'Show All'
    assert tsw_tvb_data.fig.layout.updatemenus[0].buttons[1].label == 'Hide All'


def test_create_plot(tsw_tvb_data):
    data = tsw_tvb_data.raw[:, :][0]
    ch_names = tsw_tvb_data.ch_names
    tsw_tvb_data.fig = None

    tsw_tvb_data.create_plot(data, ch_names)
    assert tsw_tvb_data.fig is not None
    assert type(tsw_tvb_data.fig) == FigureWidgetResampler

    assert len(tsw_tvb_data.fig.data) == 76
    assert len(tsw_tvb_data.fig.layout.annotations) == 76
    assert tsw_tvb_data.fig.layout.annotations[0]['text'] == 'sig 75'    # list is reversed

    assert len(tsw_tvb_data.fig.layout.updatemenus[0].buttons) == 2
    assert tsw_tvb_data.fig.layout.updatemenus[0].buttons[0].label == 'Show All'
    assert tsw_tvb_data.fig.layout.updatemenus[0].buttons[1].label == 'Hide All'


# ================================================= SCALING ========================================================
def test_setup_scaling_slider(tsw_tvb_data):
    tsw_tvb_data._setup_scaling_slider
    assert tsw_tvb_data.scaling_slider.min == 1
    assert tsw_tvb_data.scaling_slider.max == 10


# ================================================ INFO AREA =======================================================
def test_create_info_area(tsw_tvb_data):
    tsw_tvb_data._create_info_area()
    info_container = tsw_tvb_data.info_and_channels_area.children[0].children[0]
    for info in info_container.children:
        assert type(info) == widgets.HTML


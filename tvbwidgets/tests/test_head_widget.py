# -*- coding: utf-8 -*-
#
# "TheVirtualBrain - Widgets" package
#
# (c) 2022-2025, TVB Widgets Team
#

import logging
import os
import numpy
import pytest

import tvbwidgets.api as api
from tvb.datatypes.connectivity import Connectivity
from tvb.datatypes.region_mapping import RegionMapping
from tvb.datatypes.sensors import SensorsInternal, Sensors
from tvb.datatypes.surfaces import FaceSurface, CorticalSurface, Surface

from tvbwidgets.core.auth import CLB_AUTH
from tvbwidgets.core.exceptions import InvalidFileException
from tvbwidgets.tests.test_drive_widget import MockDriveClient
from tvbwidgets.ui.head_widget import HeadBrowser

NOT_SUPPORTED = 'not supported'


def test_add_datatype(caplog, mocker):
    def mock_update_plot(self):
        """Mock plot drawing"""
        pass

    mocker.patch('tvbwidgets.ui.head_widget.CustomOutput.update_plot', mock_update_plot)

    logger = logging.getLogger('tvbwidgets')
    logger.propagate = True

    connectivity = Connectivity(centres=numpy.zeros((10, 3)))
    widget = api.HeadWidget([connectivity])
    assert widget.output_plot.total_actors == 1
    assert len(widget.plot_controls.children) == 1

    caplog.clear()
    with caplog.at_level(logging.DEBUG):
        api.HeadWidget(None)
        assert len(caplog.records) == 0

    caplog.clear()
    with caplog.at_level(logging.DEBUG):
        api.HeadWidget('abc')
        assert caplog.records[0].levelname == 'WARNING'
        assert NOT_SUPPORTED in caplog.text

    caplog.clear()
    with caplog.at_level(logging.DEBUG):
        api.HeadWidget([10])
        assert caplog.records[0].levelname == 'WARNING'
        assert NOT_SUPPORTED in caplog.text

    widget = api.HeadWidget()

    caplog.clear()
    with caplog.at_level(logging.DEBUG):
        widget.add_datatype(None)
        assert caplog.records[0].levelname == 'INFO'
        assert 'None' in caplog.text

    caplog.clear()
    widget.add_datatype(RegionMapping())
    assert caplog.records[0].levelname == 'INFO'
    assert 'cmap' in caplog.text

    caplog.clear()
    widget.add_datatype(10)
    assert caplog.records[0].levelname == 'WARNING'
    assert NOT_SUPPORTED in caplog.text

    widget.add_datatype(connectivity)
    assert widget.output_plot.total_actors == 1
    assert len(widget.plot_controls.children) == 1

    face = FaceSurface(vertices=numpy.zeros((10, 3)), triangles=numpy.zeros((10, 3), dtype=int))
    widget.add_datatype(face)
    assert widget.output_plot.total_actors == 2
    assert len(widget.plot_controls.children) == 2

    seeg = SensorsInternal(locations=numpy.zeros((10, 3)))
    widget.add_datatype(seeg)
    assert widget.output_plot.total_actors == 3
    assert len(widget.plot_controls.children) == 3

    cortex = CorticalSurface(vertices=numpy.zeros((10, 3)), triangles=numpy.zeros((10, 3), dtype=int))
    reg_map = RegionMapping(array_data=numpy.zeros(10, dtype=int))
    config = api.HeadWidgetConfig(name='Cortex')
    config.add_region_mapping_as_cmap(reg_map)
    widget.add_datatype(cortex)
    assert widget.output_plot.total_actors == 4
    assert len(widget.plot_controls.children) == 4

    left_spots = widget.output_plot.MAX_ACTORS - widget.output_plot.total_actors

    caplog.clear()
    for _ in range(left_spots + 1):
        widget.add_datatype(connectivity)
    assert caplog.records[0].levelname == 'INFO'
    assert 'reached the maximum' in caplog.text

    logger.propagate = False


def test_head_widget(mocker):
    def mockk(token):
        return MockDriveClient()

    mocker.patch('ebrains_drive.connect', mockk)

    if os.environ.get(CLB_AUTH):
        os.environ.pop(CLB_AUTH)

    with pytest.raises(RuntimeError):
        HeadBrowser()

    os.environ[CLB_AUTH] = "test_auth_token"
    widget = HeadBrowser()

    assert len(widget.buttons.children) == 3

    with pytest.raises(InvalidFileException):
        widget._TVBWidgetWithBrowser__validate_file(None, None)

    with pytest.raises(InvalidFileException):
        widget._TVBWidgetWithBrowser__validate_file('abc.txt', '.zip')

    widget._TVBWidgetWithBrowser__display_message('ABC')
    assert widget.message_label.value == HeadBrowser.MSG_TEMPLATE.format('ABC', HeadBrowser.MSG_COLOR)

    widget.storage_widget.drive_api.repos_dropdown.value = widget.storage_widget.drive_api.repos_dropdown.options['repo1']
    widget.storage_widget.drive_api.files_list.value = widget.storage_widget.drive_api.files_list.options[1]

    widget.load_selected_file(Surface)
    assert 'Only .zip' in widget.message_label.value

    widget.load_selected_file(Sensors, '.txt')
    assert 'Could not load' in widget.message_label.value

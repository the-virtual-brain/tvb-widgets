# -*- coding: utf-8 -*-
#
# "TheVirtualBrain - Widgets" package
#
# (c) 2022-2023, TVB Widgets Team
#
import json
import os

import numpy
import pytest
import shutil
import tempfile

from tvbwidgets.exporters.model_exporters import JSONModelExporter
from tvbwidgets.ui.phase_plane_widget import PhasePlaneWidget
from tvb.simulator.models.oscillator import Generic2dOscillator, SupHopf
from tvbwidgets.tests.constants import OSCILLATOR_2d_DEFAULT_CONFIG


@pytest.fixture
def temp_storage():
    """
    returns a temp dir and path to a json file in the temp dir
    after each test the temp dir is removed
    """
    temp_storage = tempfile.mkdtemp()
    file_path = os.path.join(temp_storage, 'test_config.json')
    yield temp_storage, file_path
    shutil.rmtree(temp_storage)


@pytest.fixture(autouse=True)
def mock_exporter_filename(temp_storage, monkeypatch):
    _storage, file = temp_storage
    monkeypatch.setattr(JSONModelExporter, 'file_name', file)


def test_josn_export_config_simple():
    """
    tests that widget exports default model configuration to a json
    """
    wid = PhasePlaneWidget(model=Generic2dOscillator(**{k: numpy.array(v) for k, v in OSCILLATOR_2d_DEFAULT_CONFIG.items() if k != 'model'}))
    wid.get_widget()
    default_config = OSCILLATOR_2d_DEFAULT_CONFIG
    wid.export_model_configuration()

    with open(JSONModelExporter.file_name, 'r') as exported_json:
        exported_config = json.loads(exported_json.read())
        assert default_config == exported_config['default_config_key1']
        assert len(exported_config.keys()) == 1


def test_json_export_with_user_defined_configuration_name():
    """
    test that widget exports configuration with a user defined name
    """
    wid = PhasePlaneWidget(model=Generic2dOscillator(**{k: numpy.array(v) for k, v in OSCILLATOR_2d_DEFAULT_CONFIG.items() if k != 'model'}))
    wid.get_widget()
    config_name = 'test_config name'
    default_config = OSCILLATOR_2d_DEFAULT_CONFIG
    wid.config_name.value = config_name
    wid.export_model_configuration()
    with open(JSONModelExporter.file_name, 'r') as exported_json:
        exported_config = json.loads(exported_json.read())
        assert default_config == exported_config[config_name]
        assert len(exported_config.keys()) == 1

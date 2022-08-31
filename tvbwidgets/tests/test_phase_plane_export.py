# -*- coding: utf-8 -*-
#
# "TheVirtualBrain - Widgets" package
#
# (c) 2022-2023, TVB Widgets Team
#
import json
import os
import pytest
import shutil
import tempfile
from tvbwidgets.ui.phase_plane_widget import PhasePlaneWidget, is_jsonable
from tvb.simulator.models.oscillator import Generic2dOscillator, SupHopf


OSCILLATOR_2d_DEFAULT_CONFIG = {
    'model': 'Generic2dOscillator',
    'tau': 1.00,
    'I': 0.00,
    'a': -2.00,
    'b': -10.00,
    'c': 0.00,
    'd': 0.02,
    'e': 3.00,
    'f': 1.00,
    'g': 0.00,
    'alpha': 1.00,
    'beta': 1.00,
    'gamma': 1.00
}


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
def mock_phaseplane_filename(temp_storage, monkeypatch):
    _storage, file = temp_storage
    monkeypatch.setattr(PhasePlaneWidget, '_get_exported_file_name', lambda _self: file)


def test_export_config():
    """
    tests that widget exports default model configuration to a json
    """
    wid = PhasePlaneWidget()
    wid.get_widget()
    default_config = OSCILLATOR_2d_DEFAULT_CONFIG
    wid.export_json_config()

    with open(wid._get_exported_file_name(), 'r') as exported_json:
        exported_config = json.loads(exported_json.read())
        assert default_config == exported_config['config_1']
        assert len(exported_config.keys()) == 1


def test_multiple_exports():
    """
    tests that export works for multiple configurations export
    """
    wid = PhasePlaneWidget()
    wid.get_widget()
    default_config = OSCILLATOR_2d_DEFAULT_CONFIG
    # export same configuration 3 times
    wid.export_json_config()
    wid.export_json_config()
    wid.export_json_config()

    with open(wid._get_exported_file_name(), 'r') as exported_json:
        exported_config = json.loads(exported_json.read())
        assert default_config == exported_config['config_1']
        assert default_config == exported_config['config_2']
        assert default_config == exported_config['config_3']
        assert len(exported_config.keys()) == 3


def test_export_with_user_defined_name():
    """
    test that widget exports configuration with a user defined name
    """
    wid = PhasePlaneWidget()
    wid.get_widget()
    config_name = 'test_config name'
    default_config = OSCILLATOR_2d_DEFAULT_CONFIG
    wid.export_config_name_input.value = config_name
    wid.export_json_config()
    with open(wid._get_exported_file_name(), 'r') as exported_json:
        exported_config = json.loads(exported_json.read())
        assert default_config == exported_config[config_name]
        assert len(exported_config.keys()) == 1


def test_changing_configuration_exports_correct_values():
    """
    tests that after changing the default config values and exporting them
    the values exported are the changed ones
    """
    wid = PhasePlaneWidget()
    wid.get_widget()
    config_default_name = 'test_config name'
    config_changed_name = 'test_config_name 2'
    default_config = OSCILLATOR_2d_DEFAULT_CONFIG
    wid.export_config_name_input.value = config_default_name
    wid.export_json_config()
    wid.export_config_name_input.value = config_changed_name
    wid.param_sliders['I'].value = 2.80
    wid.export_json_config()
    with open(wid._get_exported_file_name(), 'r') as exported_json:
        exported_config = json.loads(exported_json.read())
        changed_config = default_config.copy()
        changed_config['I'] = 2.80
        assert default_config == exported_config[config_default_name]
        assert changed_config == exported_config[config_changed_name]
        assert len(exported_config.keys()) == 2


def test_with_suphopf_model():
    """
    tests that export works with other model than Generic2dOscillator
    """
    wid = PhasePlaneWidget(model=SupHopf())
    wid.get_widget()
    default_config = wid.param_sliders_values
    default_config['model'] = 'SupHopf'
    wid.export_json_config()
    with open(wid._get_exported_file_name(), 'r') as exported_json:
        exported_config = json.loads(exported_json.read())
        assert default_config == exported_config['config_1']
        assert len(exported_config.keys()) == 1


def test_is_jsonable():
    """
    tests that function works for serializable objects and fails for non-serializable objects
    """
    text = 'some text'
    number = 123.123
    some_list = [1, 1.23, -123]
    some_dict = {'text': text, 'number': number, 'some_list': some_list}
    assert is_jsonable(text)
    assert is_jsonable(number)
    assert is_jsonable(some_list)
    assert is_jsonable(some_dict)
    assert not is_jsonable(PhasePlaneWidget)
    assert not is_jsonable(Generic2dOscillator())

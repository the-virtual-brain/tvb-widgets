# -*- coding: utf-8 -*-
#
# "TheVirtualBrain - Widgets" package
#
# (c) 2022-2025, TVB Widgets Team
#

import json
import os
import numpy
import pytest
import shutil
import tempfile
from tvbwidgets.core.simulator.model_exporters import is_jsonable, is_valid_file_name, JSONModelExporter, PythonCodeExporter
from tvb.simulator.models.oscillator import Generic2dOscillator, SupHopf
from tvbwidgets.tests.constants import SUP_HOPF_DEFAULT_PARAMS, OSCILLATOR_2d_DEFAULT_CONFIG


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
    assert not is_jsonable(SupHopf)
    assert not is_jsonable(Generic2dOscillator())


def test_is_valid_file_name():
    assert is_valid_file_name('some_py_file')
    assert is_valid_file_name('some_py_file.py')
    assert is_valid_file_name('somefile')
    assert not is_valid_file_name('some_py_file/')
    assert not is_valid_file_name('some_,py_file')


@pytest.fixture
def temp_storage():
    temp_storage = tempfile.mkdtemp()
    file_path = os.path.join(temp_storage)
    yield temp_storage, file_path
    shutil.rmtree(temp_storage)


class TestJSONModelExporter:

    @pytest.fixture(autouse=True)
    def mock_exported_filename(self, temp_storage, monkeypatch):
        _storage, file = temp_storage
        file_json_path = os.path.join(file, 'test_json.json')
        monkeypatch.setattr(JSONModelExporter, 'file_path', file_json_path)

    def _export_sup_hopf_default(self):
        model = SupHopf(a=numpy.array(SUP_HOPF_DEFAULT_PARAMS['a']),
                        omega=numpy.array(SUP_HOPF_DEFAULT_PARAMS['omega']))
        keys = ['a', 'omega']
        exporter = JSONModelExporter(model, keys)
        exporter.do_export()
        return exporter

    def test_simple_sup_hopf_export(self):
        exporter = self._export_sup_hopf_default()
        with open(exporter.file_path, 'r') as file:
            json_content = json.loads(file.read())
            assert json_content[exporter.default_config_name + '1'] == SUP_HOPF_DEFAULT_PARAMS

    def test_multiple_sup_hopf_exports(self):
        exporter = self._export_sup_hopf_default()
        exporter.do_export()
        with open(exporter.file_path, 'r') as file:
            json_content = json.loads(file.read())
            assert len(json_content.keys()) == 2
            assert json_content[exporter.default_config_name + '1'] == SUP_HOPF_DEFAULT_PARAMS
            assert json_content[exporter.default_config_name + '2'] == SUP_HOPF_DEFAULT_PARAMS

    def test_multiple_different_exports(self):
        exporter = self._export_sup_hopf_default()
        model_2 = SupHopf(a=numpy.array([-0.2]),
                          omega=numpy.array(SUP_HOPF_DEFAULT_PARAMS['omega']))
        exporter.model_instance = model_2
        exporter.do_export()
        with open(exporter.file_path, 'r') as file:
            json_content = json.loads(file.read())
            assert len(json_content.keys()) == 2
            assert json_content[exporter.default_config_name + '1'] == SUP_HOPF_DEFAULT_PARAMS
            copy_config = SUP_HOPF_DEFAULT_PARAMS.copy()
            copy_config['a'] = [-0.2]
            assert json_content[exporter.default_config_name + '2'] == copy_config

    def test_multiple_exports_different_models(self):
        exporter = self._export_sup_hopf_default()
        generic_defaults = {key: numpy.array(value) for key, value in OSCILLATOR_2d_DEFAULT_CONFIG.items() if
                            key != 'model'}
        exporter.model_instance = Generic2dOscillator(**generic_defaults)
        exporter.keys = generic_defaults.keys()
        exporter.do_export()
        with open(exporter.file_path, 'r') as file:
            json_content = json.loads(file.read())
            assert json_content[exporter.default_config_name + '1'] == SUP_HOPF_DEFAULT_PARAMS
            assert json_content[exporter.default_config_name + '2'] == OSCILLATOR_2d_DEFAULT_CONFIG


class TestPythonCodeExporter:
    @pytest.fixture(autouse=True)
    def mock_exported_filename(self, temp_storage, monkeypatch):
        _storage, file = temp_storage
        py_file_path = os.path.join(file, 'instances_test_python.py')
        monkeypatch.setattr(PythonCodeExporter, 'file_path', py_file_path)

    def test_simple_sup_hopf_python_export(self):
        args = {k: numpy.array(v) for k, v in SUP_HOPF_DEFAULT_PARAMS.items() if k != 'model'}
        model_instance = SupHopf(**args)
        exporter = PythonCodeExporter(model_instance, args.keys())
        exporter.do_export()
        expected = '# default config\nimport numpy\nfrom tvb.simulator import models\n' \
                   'model_instance = models.SupHopf(a=numpy.array([-0.5]),omega=numpy.array([1.]))\n' \
                   'model_instance\n\n'
        with open(exporter.file_path, 'r') as file:
            py_content = file.read()
            assert py_content == expected

    def test_multiple_sup_hopf_py_export(self):
        args = {k: numpy.array(v) for k, v in SUP_HOPF_DEFAULT_PARAMS.items() if k != 'model'}
        model_instance = SupHopf(**args)
        exporter = PythonCodeExporter(model_instance, args.keys())
        exporter.do_export()
        exporter.do_export()
        expected = '# default config\nimport numpy\nfrom tvb.simulator import models\n' \
                   'model_instance = models.SupHopf(a=numpy.array([-0.5]),omega=numpy.array([1.]))\n' \
                   'model_instance\n\n'
        expected += '# default config\n' \
                    'model_instance = models.SupHopf(a=numpy.array([-0.5]),omega=numpy.array([1.]))\n' \
                    'model_instance\n\n'

        with open(exporter.file_path, 'r') as file:
            py_content = file.read()
            assert py_content == expected

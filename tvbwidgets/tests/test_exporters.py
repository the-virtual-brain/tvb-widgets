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
from tvbwidgets.exporters.model_exporters import is_jsonable, is_valid_file_name, JSONModelExporter
from tvb.simulator.models import Generic2dOscillator, SupHopf

SUP_HOPF_DEFAULT_PARAMS = {
    'a': [-0.5],
    'omega': [1],
    'model': 'SupHopf'
}


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
    def mock_phaseplane_filename(self, temp_storage, monkeypatch):
        _storage, file = temp_storage
        file_json_path = os.path.join(file, 'test_json.json')
        monkeypatch.setattr(JSONModelExporter, 'file_name', file_json_path)

    def test_simple_sup_hopf_export(self):
        model = SupHopf()
        keys = ['a', 'omega']
        exporter = JSONModelExporter(model, keys)
        exporter.do_export()
        with open(exporter.file_name, 'r') as file:
            json_content = json.loads(file.read())
            assert json_content[exporter.default_config_name + '1'] == SUP_HOPF_DEFAULT_PARAMS


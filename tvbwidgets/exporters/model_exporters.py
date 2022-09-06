import abc
import json
import numpy
import os
import re
from tvb.simulator.models import Model

from tvbwidgets.core.exceptions import ModelExporterNotFoundError

MODEL_CONFIGURATION_EXPORTS = {
    'JSON': 'json',
    'Python script': 'python'
}


def is_valid_file_name(filename: str) -> bool:
    """
    checks if a string is valid python file name
    returns even if the file doesn't end with .py
    """
    patterns = [re.compile(r'\w+.py+$'), re.compile(r'\w+$')]
    return any([re.match(p, filename) for p in patterns])


class ABCModelExporter(abc.ABC):
    @abc.abstractmethod
    def __init__(self, model_instance: Model, keys: list[str]):
        self.model_instance = model_instance
        self.keys = keys
        # name of the exported configuration is set
        # from outside of class if we need other name than the default
        self.config_name = self.default_config_name

    @property
    @abc.abstractmethod
    def default_config_name(self):
        """
        default name of the configuration to be exported
        """
        pass

    @abc.abstractmethod
    def do_export(self):
        """
        implements export logic
        """
        pass

    @staticmethod
    def sanitize_property(prop: any) -> any:
        """
        makes property safe for json serialization while allowing serialization of numpy arrays as lists
        """
        if is_jsonable(prop):
            return prop
        if isinstance(prop, numpy.ndarray):
            return prop.tolist()
        return prop.__class__.__name__


class JSONModelExporter(ABCModelExporter):
    """
    Class used to export a model configuration to json format
    """
    file_name = 'model_config.json'

    def __init__(self, model_instance, keys: list[str]):
        super(JSONModelExporter, self).__init__(model_instance, keys)

    @property
    def default_config_name(self):
        return 'default_config_key'

    def do_export(self):
        config_dict = self._read_existing_config()
        config_name = self.config_name if self.config_name != self.default_config_name else self.default_config_name + str(len(config_dict.keys()) + 1)
        config_dict[config_name] = self._prepare_export_values()
        with open(self.file_name, 'w') as f:
            f.write(json.dumps(config_dict))

    def _read_existing_config(self) -> dict:
        """
        reads a json file and returns the dict representing the json data as dict or an empty dict
        if the config file or data in it doesn't exist
        """
        file_name = self.file_name
        config = {}
        try:
            with open(file_name, 'r+') as config_file:
                config = json.loads(config_file.read())
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        return config

    def _prepare_export_values(self):
        values = {}
        model_dict = self.model_instance.__dict__

        for key in self.keys:
            if model_dict.get(key, False):
                values[key] = self.sanitize_property(model_dict[key])

        values['model'] = self.model_instance.__class__.__name__

        return values


class PythonCodeExporter(ABCModelExporter):
    file_name = 'model_instances.py'
    models_import = 'tvb.simulator.lab.models'

    def __init__(self, model_instance, keys: list[str]):
        super(PythonCodeExporter, self).__init__(model_instance, keys)

    @property
    def default_config_name(self):
        return 'default config'

    def do_export(self):
        class_name = self.model_instance.__class__.__name__
        values = f'# {self.config_name}\n'
        # assume that if the file exists the imports also exist
        if not os.path.exists(self.file_name):
            values += f'import numpy\nfrom {self.models_import} import *\n'

        model_params = self.get_model_params()
        values += f'model_instance = {class_name}({model_params})\n\n'

        # open the file to append to existing saved model instances
        with open(self.file_name, 'a') as f:
            f.write(values)

    def get_model_params(self):
        model_params = ''
        model_instance_dict = self.model_instance.__dict__

        for key in self.keys:
            if model_instance_dict.get(key, False):
                model_params += f'{key}=numpy.array({model_instance_dict[key]}),'
        # strip the last comma on params before returning
        return model_params.rstrip(model_params[-1])


def model_exporter_factory(exporter_type: str, model: Model, keys: list[str]) -> ABCModelExporter:
    exporter = MODEL_CONFIGURATION_EXPORTS.get(exporter_type, False)

    if not exporter:
        raise ModelExporterNotFoundError('Could not find any exporter of the selected type!')

    if exporter == 'python':
        return PythonCodeExporter(model, keys)

    return JSONModelExporter(model, keys)


def is_jsonable(x: any):
    """
    checks if an object is serializable
    """
    try:
        json.dumps(x)
        return True
    except (TypeError, OverflowError):
        return False

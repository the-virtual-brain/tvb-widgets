# -*- coding: utf-8 -*-
#
# "TheVirtualBrain - Widgets" package
#
# (c) 2022-2023, TVB Widgets Team
#

import abc
import json
import numpy
import os
import re
from enum import Enum
from tvb.simulator.models import Model

from tvbwidgets import get_logger
from tvbwidgets.core.exceptions import ModelExporterNotFoundError


class ModelConfigurationExports(Enum):
    JSON = 'JSON'
    PYTHON = 'Python script'


def is_valid_file_name(filename):
    # type: (str) -> bool
    """
    checks if a string is valid python file name
    returns even if the file doesn't end with .py
    """
    patterns = [re.compile(r'\w+.py+$'), re.compile(r'\w+$')]
    return any([re.match(p, filename) for p in patterns])


class ABCModelExporter(abc.ABC):
    @abc.abstractmethod
    def __init__(self, model_instance, keys):
        # type: (Model, list[str]) -> None
        """
        Abstract constructor to be implemented in subclasses
        """
        self.model_instance = model_instance
        self.keys = keys
        # name of the exported configuration is set
        # from outside of class if we need other name than the default
        self.config_name = self.default_config_name
        self.logger = get_logger(self.__class__.__module__)

    @property
    @abc.abstractmethod
    def default_config_name(self):
        # type: () -> str
        """
        Abstract property to be implemented in subclasses representing
        default name of the configuration to be exported
        """
        pass

    @abc.abstractmethod
    def do_export(self):
        """
        Abstract method to be implemented in subclasses
        implements export logic
        """
        pass

    @staticmethod
    def sanitize_property(prop: any) -> any:
        # type: (any) -> any
        """
        makes property safe for json serialization while allowing serialization
        of numpy arrays as lists
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

    def __init__(self, model_instance, keys):
        # type: (Model, list[str]) -> None
        super(JSONModelExporter, self).__init__(model_instance, keys)

    @property
    def default_config_name(self):
        return 'default_config_key'

    def do_export(self):
        """
        exports model params and model name as json under the key config_name
        if that is different to the default key or the default key plus length of the existing keys
        in the json file + 1
        """
        config_dict = self._read_existing_config()
        config_name = self.config_name if self.config_name != self.default_config_name else self.default_config_name + str(len(config_dict.keys()) + 1)
        config_dict[config_name] = self._prepare_export_values()
        with open(self.file_name, 'w') as f:
            f.write(json.dumps(config_dict))

    def _read_existing_config(self):
        # type: () -> dict
        """
        reads a json file and returns the dict representing the json data or an empty dict
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
        # type: () -> dict
        """
        returns a json safe dict containing the model params from the exporter keys
        """
        values = {}
        model_dict = self.model_instance.__dict__

        for key in self.keys:
            try:
                values[key] = self.sanitize_property(model_dict[key])
            except KeyError:
                self.logger.warning(
                    f'Parameter {key} will be skipped, it does not exist on {type(self.model_instance)}')

        values['model'] = self.model_instance.__class__.__name__

        return values


class PythonCodeExporter(ABCModelExporter):
    file_name = 'model_instances.py'
    numpy_import = 'import numpy'
    module_name = 'models'
    models_import = f'from tvb.simulator import {module_name}'
    instance_var_name = 'model_instance'

    def __init__(self, model_instance, keys):
        # type: (Model, list[str]) -> None
        super(PythonCodeExporter, self).__init__(model_instance, keys)

    @property
    def default_config_name(self):
        return 'default config'

    def do_export(self):
        class_name = self.model_instance.__class__.__name__
        values = f'# {self.config_name}\n'
        # assume that if the file exists the imports also exist
        if not os.path.exists(self.file_name):
            values += f'{self.numpy_import}\n{self.models_import}\n'

        model_params = self.get_model_params()
        values += f'{self.instance_var_name} = {self.module_name}.{class_name}({model_params})\n\n'

        # open the file to append to existing saved model instances
        with open(self.file_name, 'a') as f:
            f.write(values)

    def get_model_params(self):
        model_params = ''
        model_instance_dict = self.model_instance.__dict__

        for key in self.keys:
            try:
                model_params += f'{key}=numpy.array({model_instance_dict[key]}),'
            except KeyError:
                self.logger.warning(
                    f'Parameter {key} will be skipped, it does not exist on {type(self.model_instance)}')
        # strip the last comma on params before returning
        return model_params.rstrip(model_params[-1])


def model_exporter_factory(exporter_type, model, keys):
    # type: (str, Model, list[str]) -> ABCModelExporter
    """
    Factory for model exporter creation
    """

    try:
        exporter = ModelConfigurationExports(exporter_type)
    except ValueError:
        raise ModelExporterNotFoundError('Could not find any exporter of the selected type!')

    if exporter == ModelConfigurationExports.PYTHON:
        return PythonCodeExporter(model, keys)

    return JSONModelExporter(model, keys)


def is_jsonable(x):
    # type: (any) -> bool
    """
    checks if an object is serializable
    """
    try:
        json.dumps(x)
        return True
    except (TypeError, OverflowError):
        return False

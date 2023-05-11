import importlib
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import toml
from tvb.basic.neotraits._attr import NArray
from tvb.datatypes.connectivity import Connectivity
from tvb.simulator.simulator import Simulator
from tvbwidgets.core.logger.builder import get_logger
LOGGER = get_logger("tvbwidgets.core.pse.parameters")


def read_from_file(file_name):
    with open(file_name, 'r') as f:
        obj = toml.load(f)
    return obj


@dataclass()
class TOMLStorage(object):

    def stage_out_simulator(self, simulator_data):
        simulator = Simulator()

        model = simulator_data["model_class"]
        models = importlib.import_module("tvb.simulator.models")
        class_model = getattr(models, model)
        simulator.model = class_model(**{k: np.r_[v[0]] for k, v in simulator_data['model_parameters'].items()})

        coupling = simulator_data["coupling_class"]
        couplings = importlib.import_module("tvb.simulator.coupling")
        class_coupling = getattr(couplings, coupling)
        simulator.coupling = class_coupling()

        simulator.simulation_length = simulator_data["length"]
        simulator.conduction_speed = simulator_data["conduction_speed"]
        voi = simulator_data['attributes'].get('variables_of_interest', None)
        if voi:
            simulator.model.variables_of_interest = voi

        stvar_range = simulator_data['attributes'].get('state_variable_range', None)
        if stvar_range:
            for k, val in stvar_range.items():
                simulator.model.state_variable_range[k] = np.array(val)
        for k in simulator_data['attributes'].keys():
            if k not in ['state_variable_range', 'variables_of_interests']:
                raise NotImplementedError(f'unsupported attribute: {k}')

        simulator.connectivity = Connectivity.from_file()
        return simulator

    def write_in_file(self, simulator, param1, param2, param1_values, param2_values, metrics, n_threads, file_name):
        data = {}
        stage_in_obj = Path("pse.toml")
        if not stage_in_obj.exists():
            stage_in_obj.touch()

        with open(stage_in_obj, "w") as f:
            data["parameters"] = {"param1": param1, "param2": param2, "metrics": metrics,
                                  "file_name": file_name, "n_threads": n_threads}

            if param1 == "connectivity":
                data["parameters"].update({"param2_values": param2_values})
                data["connectivity"] = {"param1_values": param1_values}

            elif param2 == "connectivity":
                data["parameters"].update({"param1_values": param1_values})
                data["connectivity"] = {"param2_values": param2_values}
            else:
                data["parameters"].update({"param1_values": param1_values, "param2_values": param2_values})

            data_sim = self.stage_in_simulator(data, simulator)
            toml.dump(data_sim, f)
        return stage_in_obj

    def stage_in_simulator(self, data, simulator):
        # TODO add the 'stvar' attribute to stage-in simulator, if needed
        data["simulator"] = {"model_parameters": {}, "attributes": {"state_variable_range": {}}}

        data["simulator"]["model_class"] = simulator.model.__class__.__name__
        data["simulator"]["coupling_class"] = simulator.coupling.__class__.__name__
        data["simulator"]["conduction_speed"] = simulator.conduction_speed
        data["simulator"]["length"] = simulator.simulation_length

        for elem in type(simulator.model).declarative_attrs:
            attribute = getattr(type(simulator.model), elem)
            if isinstance(attribute, NArray):
                values_list = getattr(simulator.model, elem).tolist()
                data["simulator"]["model_parameters"].update({elem: values_list})

        data["simulator"]["attributes"]["variables_of_interests"] = simulator.model.variables_of_interest

        items = simulator.model.state_variable_range
        for elem in items.keys():
            data["simulator"]["attributes"]["state_variable_range"][elem] = items[elem].tolist()
        return data

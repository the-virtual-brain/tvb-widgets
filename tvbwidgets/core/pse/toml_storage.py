# -*- coding: utf-8 -*-
#
# "TheVirtualBrain - Widgets" package
#
# (c) 2022-2023, TVB Widgets Team
#

import toml
import importlib
import numpy as np
from pathlib import Path
from datetime import datetime
from tvb.basic.neotraits._attr import NArray
from tvb.datatypes.connectivity import Connectivity
from tvb.simulator.simulator import Simulator


class TOMLStorage:

    @staticmethod
    def read_pse_from_file(file_name):

        with open(file_name, 'r') as f:
            obj = toml.load(f)

        param1 = obj["parameters"]["param1"]
        param2 = obj["parameters"]["param2"]
        if param1 != "connectivity":
            param1_values = [float(elem) for elem in obj["parameters"]["param1_values"]]
        else:
            param1_values = [Connectivity.from_file(elem) for elem in obj["connectivity"]["param1_values"]]
        if param2 != "connectivity":
            param2_values = [float(elem) for elem in obj["parameters"]["param2_values"]]
        else:
            param2_values = [Connectivity.from_file(elem) for elem in obj["connectivity"]["param2_values"]]
        metrics = obj["parameters"]["metrics"]
        file_name = obj["parameters"]["file_name"]
        n_threads = obj["parameters"]["n_threads"]

        simulator = TOMLStorage._stage_out_simulator(obj["simulator"])
        return param1, param1_values, param2, param2_values, metrics, file_name, n_threads, simulator

    @staticmethod
    def _stage_out_simulator(simulator_data):
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

        # Here we might have various other loading mechanisms for the conn - such as from Siibra
        if 'connectivity_from_file' in simulator_data:
            from_file = simulator_data["connectivity_from_file"]
            simulator.connectivity = Connectivity.from_file(from_file)
        else:
            simulator.connectivity = Connectivity.from_file()
        return simulator

    @staticmethod
    def write_pse_in_file(simulator, param1, param2, param1_values, param2_values, metrics, n_threads, file_name):
        data = {}
        stage_in_obj = Path(f"pse_{datetime.now().strftime('%Y%m%d_%H%M%S')}.toml")
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

            data_sim = TOMLStorage._stage_in_simulator(data, simulator)
            toml.dump(data_sim, f)
        return stage_in_obj

    @staticmethod
    def _stage_in_simulator(data, simulator):
        # type (dict, Simulator) -> dict
        # TODO add the 'stvar' attribute to stage-in simulator, if needed
        data["simulator"] = {"model_parameters": {}, "attributes": {"state_variable_range": {}}}

        simulator.configure()
        data["simulator"]["model_class"] = simulator.model.__class__.__name__
        data["simulator"]["coupling_class"] = simulator.coupling.__class__.__name__
        data["simulator"]["conduction_speed"] = simulator.conduction_speed
        data["simulator"]["length"] = simulator.simulation_length
        # TODO this is far from ideal for a Connectivity
        data["simulator"]["connectivity_from_file"] = f"connectivity_{simulator.connectivity.number_of_regions}.zip"

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

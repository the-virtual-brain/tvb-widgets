# -*- coding: utf-8 -*-
#
# "TheVirtualBrain - Widgets" package
#
# (c) 2022-2023, TVB Widgets Team
#

from dataclasses import dataclass
from tvb.datatypes.connectivity import Connectivity
from tvb.simulator.simulator import Simulator


@dataclass
class StoreObj(object):
    sim: Simulator
    param1: str
    param2: str
    param1_values: list[float | str | Connectivity]
    param2_values: list[float | str | Connectivity]
    metrics: list[str]
    n_threads: int
    file_name: str

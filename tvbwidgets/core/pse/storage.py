# -*- coding: utf-8 -*-
#
# "TheVirtualBrain - Widgets" package
#
# (c) 2022-2025, TVB Widgets Team
#

from dataclasses import dataclass
from tvb.simulator.simulator import Simulator


@dataclass
class StoreObj(object):
    sim: Simulator
    param1: str
    param2: str
    param1_values: list
    param2_values: list
    metrics: list
    n_threads: int
    file_name: str

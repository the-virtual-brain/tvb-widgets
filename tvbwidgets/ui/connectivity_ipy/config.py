# -*- coding: utf-8 -*-
#
# "TheVirtualBrain - Widgets" package
#
# (c) 2022-2025, TVB Widgets Team
#
from dataclasses import dataclass
from numpy import ndarray


@dataclass
class ConnectivityConfig:
    name: str = 'Connectivity'
    style: str = 'Points'
    points_color: str = 'Green'
    edge_color: str = 'White'
    light: bool = True
    size = [500, 500]  # [width, height]
    point_size: int = 20

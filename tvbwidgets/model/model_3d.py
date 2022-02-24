# -*- coding: utf-8 -*-
#
# "TheVirtualBrain - Widgets" package
#
# (c) 2022-2023, TVB Widgets Team
#

import numpy as np


class Model3D(object):

    def __init__(self, vertices_content=None, triangles_content=None):
        self.vertices = None
        self.triangles = None
        self.update_surface(vertices_content, triangles_content)

    def update_surface(self, vertices_str, triangles_str):
        if vertices_str is None or triangles_str is None:
            return

        self.vertices = np.loadtxt(vertices_str, dtype=np.float64, skiprows=0)
        self.triangles = np.loadtxt(triangles_str, dtype=np.int64, skiprows=0)

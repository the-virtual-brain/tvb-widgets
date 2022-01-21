from io import StringIO

import numpy as np


class Model3D(object):

    def __init__(self, vertices_content=None, triangles_content=None):
        self.vertices = None
        self.triangles = None
        self.update_surface(vertices_content, triangles_content)

    def update_surface(self, vertices_content, triangles_content):
        if vertices_content is None or triangles_content is None:
            return

        vertices_str = StringIO(vertices_content.decode())
        triangles_str = StringIO(triangles_content.decode())

        self.vertices = np.loadtxt(vertices_str, dtype=np.float64, skiprows=0)
        self.triangles = np.loadtxt(triangles_str, dtype=np.int64, skiprows=0)

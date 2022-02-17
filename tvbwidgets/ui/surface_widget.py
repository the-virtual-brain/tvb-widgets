# -*- coding: utf-8 -*-
#
# "TheVirtualBrain - Widgets" package
#
# (c) 2022-2023, TVB Widgets Team
#

import numpy
import pyvista
import ipywidgets
from io import StringIO
from tvbwidgets.model.model_3d import Model3D
from tvbwidgets.ui.base_widget import TVBWidget
from tvbwidgets.ui.storage_widget import StorageWidget

pyvista.global_theme.jupyter_backend = 'ipygany'


class SurfaceWidget(ipywidgets.VBox, TVBWidget):

    def __init__(self, **kwargs):
        self.storage_widget = StorageWidget()
        self.view_button = ipywidgets.Button(description="View")
        self.model_3d = Model3D()
        self.output = ipywidgets.Output()
        self.plotter = pyvista.Plotter()

        def view_action(s):
            vertices_content, triangles_content = self._get_surface_contents()
            self.model_3d.update_surface(vertices_content, triangles_content)
            with self.output:
                a = numpy.full((self.model_3d.triangles.shape[0], 1), 3, dtype=int)
                faces = numpy.hstack((a, self.model_3d.triangles))
                cloud = pyvista.PolyData(self.model_3d.vertices, faces=faces)
                self.plotter.clear()
                self.plotter.add_mesh(cloud)
                self.plotter.show()

        self.view_button.on_click(view_action)

        super().__init__([self.storage_widget, self.view_button, self.output], **kwargs)

    def _get_surface_contents(self):
        vertices_content = self.storage_widget.get_file_content('vertices.txt')
        triangles_content = self.storage_widget.get_file_content('triangles.txt')
        vertices_str = StringIO(vertices_content.decode())
        triangles_str = StringIO(triangles_content.decode())
        return vertices_str, triangles_str

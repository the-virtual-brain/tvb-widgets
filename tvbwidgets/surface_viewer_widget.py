import ipywidgets
import numpy
import pyvista

from tvbwidgets.model_3d import Model3D
from tvbwidgets.repo_browser_widget import RepoBrowserWidget

pyvista.global_theme.jupyter_backend = 'ipygany'


class SurfaceViewer(object):
    def __init__(self):
        self.repo_browser = RepoBrowserWidget()

        self.view_button = ipywidgets.Button(description="View")

        self.model_3d = Model3D()
        self.output = ipywidgets.Output()
        self.plotter = pyvista.Plotter()

        def view_action(s):
            vertices_content, triangles_content = self.get_surface_contents()

            self.model_3d.update_surface(vertices_content, triangles_content)
            with self.output:
                a = numpy.full((self.model_3d.triangles.shape[0], 1), 3, dtype=int)
                faces = numpy.hstack((a, self.model_3d.triangles))

                cloud = pyvista.PolyData(self.model_3d.vertices, faces=faces)
                self.plotter.clear()
                self.plotter.add_mesh(cloud)
                self.plotter.show()

        self.view_button.on_click(view_action)

    def get_widget(self):
        vbox = ipywidgets.VBox([self.repo_browser.get_widget(), self.view_button, self.output])
        return vbox

    def get_surface_contents(self):
        repo_name = self.repo_browser.get_chosen_repo().name
        vertices_filename = repo_name + '-' + 'vertices.txt'
        triangles_filename = repo_name + '-' + 'triangles.txt'

        vertices_content = self.repo_browser.get_file_content(vertices_filename)
        triangles_content = self.repo_browser.get_file_content(triangles_filename)
        return vertices_content, triangles_content

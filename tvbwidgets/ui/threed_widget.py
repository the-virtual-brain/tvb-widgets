# -*- coding: utf-8 -*-
#
# "TheVirtualBrain - Widgets" package
#
# (c) 2022-2023, TVB Widgets Team
#

import ipywidgets
import numpy
import pyvista
from ipywidgets import Output, VBox
from pyvista import PolyData
from tvb.datatypes.connectivity import Connectivity
from tvb.datatypes.region_mapping import RegionMapping
from tvb.datatypes.sensors import Sensors
from tvb.datatypes.surfaces import CorticalSurface, FaceSurface, Surface

from tvbwidgets.ui.base_widget import TVBWidget

pyvista.set_jupyter_backend('pythreejs')


class CustomOutput(Output):

    def __init__(self, plotter, **kwargs):
        super().__init__(**kwargs)
        self.plotter = plotter


class ThreeDWidget(ipywidgets.HBox, TVBWidget):

    def __init__(self, cortical_surface, face_surface=None, connectivity=None, sensors=None, region_mapping=None):
        # type: (CorticalSurface, FaceSurface, Connectivity, list[Sensors]) -> None
        if cortical_surface is None:
            raise AttributeError("The cortical surface is required for this widget, please provide one!")
        self.cortical_mesh = self.__prepare_mesh(cortical_surface)
        self.face_mesh = self.__prepare_mesh(face_surface)
        self.connectivity_points = self.__prepare_connectivity_point(connectivity)
        self.sensors_dict = self.__prepare_sensors_points(sensors)
        self.region_mapping = self.__prepare_region_mapping(region_mapping)

        self.output_plot = self.__prepare_plot()
        self.plot_controls = self.__prepare_plot_controls()
        hbox_cortex_controls = self.__prepare_cortical_controls()
        vbox = VBox([hbox_cortex_controls, self.output_plot])

        super().__init__([self.plot_controls, vbox], **{})

    def __prepare_mesh(self, surface):
        # type: (Surface) -> PolyData
        if surface is None:
            return None

        dim_4th = numpy.full((surface.triangles.shape[0], 1), 3, dtype=int)
        faces = numpy.hstack((dim_4th, surface.triangles))

        mesh = PolyData(surface.vertices, faces)
        return mesh

    def __prepare_sensors_points(self, sensors):
        # type: (typing.Union[Sensors, list[Sensors]]) -> dict
        if sensors is None:
            return None

        if type(sensors) in (tuple, list):
            points_list = {current_sensors.sensors_type: current_sensors.locations for current_sensors in sensors}
            return points_list

        return {sensors.sensors_type: sensors.locations}

    def __prepare_connectivity_point(self, connectivity):
        # type: (Connectivity) -> numpy.ndarray
        if connectivity is None:
            return None

        return connectivity.centres

    def __prepare_region_mapping(self, region_mapping):
        # type: (RegionMapping) -> numpy.ndarray
        if region_mapping is None:
            return None

        return region_mapping.array_data

    def __prepare_plotter(self):
        plotter = pyvista.Plotter()

        self.cortical_actor = plotter.add_mesh(self.cortical_mesh, name='Cortex', style='surface',
                                               scalars=self.region_mapping, cmap="fire", lighting=True)
        if self.face_mesh is not None:
            self.face_actor = plotter.add_mesh(self.face_mesh, name='Face', style='surface', color='white',
                                               lighting=True,
                                               opacity=0.2)

        if self.connectivity_points is not None:
            self.connectivity_actor = plotter.add_points(self.connectivity_points, name='Connectivity', color='green',
                                                         point_size=3000)

        if self.sensors_dict is not None:
            for (type, points) in self.sensors_dict.items():
                sensors_actor = plotter.add_points(points, name=type, color='pink', point_size=2000,
                                                   render_points_as_spheres=True)
                # TODO: keep list of actors?
                self.seeg_actor = sensors_actor

        plotter.camera.zoom(2)
        return plotter

    def __prepare_plot_controls(self):
        label = ipywidgets.Label('Display controls: ')
        hbox_checkboxes = ipywidgets.VBox((label,))

        def toggle_surface(value, actor):
            if value is True:
                self.output_plot.plotter.add_actor(actor)
            else:
                self.output_plot.plotter.renderer.remove_actor(actor, render=False)
            with self.output_plot:
                self.output_plot.clear_output(wait=True)
                self.output_plot.plotter.show()

        def toggle_face(change):
            if change.type == 'change':
                toggle_surface(change.new, self.face_actor)

        def toggle_cortex(change):
            if change.type == 'change':
                toggle_surface(change.new, self.cortical_actor)

        def toggle_seeg(change):
            if change.type == 'change':
                toggle_surface(change.new, self.seeg_actor)

        checkbox = ipywidgets.Checkbox(description="Toggle Cortex", value=True)
        checkbox.observe(toggle_cortex, names=['value'])
        hbox_checkboxes.children += checkbox,

        if self.face_mesh:
            checkbox = ipywidgets.Checkbox(description="Toggle Face", value=True)
            checkbox.observe(toggle_face, names=['value'])
            hbox_checkboxes.children += checkbox,

        if self.sensors_dict:
            checkbox = ipywidgets.Checkbox(description="Toggle SEEG", value=True)
            checkbox.observe(toggle_seeg, names=['value'])
            hbox_checkboxes.children += checkbox,

        return hbox_checkboxes

    def __prepare_cortical_controls(self):
        cortex_type = ipywidgets.ToggleButtons(options=['Surface', 'Wireframe', 'Points'],
                                               description='Cortex controls:',
                                               disabled=False)

        def toggle_cortex_type(change):
            if change['new'] == 'Wireframe':
                self.cortical_actor.GetProperty().SetRepresentationToWireframe()
            elif change['new'] == 'Surface':
                self.cortical_actor.GetProperty().SetRepresentationToSurface()
            else:
                self.cortical_actor.GetProperty().SetRepresentationToPoints()

            with self.output_plot:
                self.output_plot.clear_output(wait=True)
                self.output_plot.plotter.show()

        cortex_type.observe(toggle_cortex_type, 'value')

        cortex_opacity = ipywidgets.FloatSlider(
            value=1,
            min=0,
            max=1.0,
            step=0.1,
            description='Opacity:',
            disabled=False,
            continuous_update=False,
            orientation='horizontal',
            readout=True,
            readout_format='.1f',
        )

        def on_opacity_change(change):
            value = change['new']
            self.cortical_actor.GetProperty().SetOpacity(value)
            with self.output_plot:
                self.output_plot.clear_output(wait=True)
                self.output_plot.plotter.show()

        cortex_opacity.observe(on_opacity_change, names='value')

        hbox_cortex_controls = ipywidgets.HBox([cortex_type, cortex_opacity])
        return hbox_cortex_controls

    def __prepare_plot(self):
        plotter = self.__prepare_plotter()
        output = CustomOutput(plotter)
        with output:
            plotter.show()

        return output

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

from tvb.basic.neotraits.api import HasTraits
from tvb.datatypes.connectivity import Connectivity
from tvb.datatypes.region_mapping import RegionMapping
from tvb.datatypes.sensors import Sensors
from tvb.datatypes.surfaces import Surface

from tvbwidgets.ui.base_widget import TVBWidget

pyvista.set_jupyter_backend('pythreejs')


class SurfaceWidgetConfig:

    def __init__(self, name='Actor', style='Surface', color='White', light=True, size=1500, cmap=None, scalars=None):
        self.name = name
        self.style = style
        self.color = color
        self.light = light
        self.size = size
        self.cmap = cmap
        self.scalars = scalars

    def add_region_mapping_as_cmap(self, region_mapping):
        # type: (RegionMapping) -> None
        self.scalars = region_mapping.array_data
        self.cmap = 'fire'


class CustomOutput(Output):
    CONFIG = SurfaceWidgetConfig()
    MAX_ACTORS = 10

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.plotter = pyvista.Plotter()
        self.total_actors = 0

    @property
    def can_draw(self):
        return self.total_actors < self.MAX_ACTORS

    def add_mesh(self, mesh, config=CONFIG):
        if config.cmap is None or config.scalars is None:
            actor = self.plotter.add_mesh(mesh, name=config.name, style=config.style, color=config.color,
                                          lighting=config.light)
        else:
            actor = self.plotter.add_mesh(mesh, name=config.name, style=config.style, scalars=config.scalars,
                                          cmap=config.cmap, lighting=config.light)
        self.total_actors += 1
        return actor

    def add_points(self, points, config=CONFIG):
        actor = self.plotter.add_points(points, name=config.name, color=config.color,
                                        point_size=config.size)
        self.total_actors += 1
        return actor

    def display_actor(self, actor):
        self.plotter.add_actor(actor)

    def hide_actor(self, actor):
        self.plotter.renderer.hide_actor(actor, render=False)

    def update_plot(self):
        with self:
            self.clear_output(wait=True)
            self.plotter.show()


class SurfaceWidget(ipywidgets.HBox, TVBWidget):

    def __init__(self, datatypes=None):
        # type: (list[HasTraits]) -> None
        self.output_plot = CustomOutput()
        self.plot_controls = self.__prepare_plot_controls()
        self.surface_display_controls = VBox()
        vbox = VBox([self.surface_display_controls, self.output_plot])

        super().__init__([self.plot_controls, vbox], **{})

        if datatypes is not None:
            if not isinstance(datatypes, list):
                self.logger.warning("Input not supported. Please provide a list of datatypes.")
            else:
                for datatype in datatypes:
                    self.add_datatype(datatype)

    def add_datatype(self, datatype, config=None):
        # type: (HasTraits, SurfaceWidgetConfig) -> None
        if datatype is None:
            self.logger.info("The provided datatype is None!")
            return

        if self.output_plot.can_draw is False:
            self.logger.info("You have reached the maximum datatypes that can be drawn to this plot!")
            return

        if isinstance(datatype, Surface):
            self.__draw_mesh_actor(datatype, config)
        elif isinstance(datatype, Connectivity):
            self.__draw_connectivity_actor(datatype, config)
        elif isinstance(datatype, Sensors):
            self.__draw_sensors_actor(datatype, config)
        elif isinstance(datatype, RegionMapping):
            self.logger.info("RegionMapping should be given as cmap in the config parameter!")
        else:
            self.logger.warning("Datatype not supported by this widget!")

    def __prepare_mesh(self, surface):
        # type: (Surface) -> PolyData
        dim_4th = numpy.full((surface.triangles.shape[0], 1), 3, dtype=int)
        faces = numpy.hstack((dim_4th, surface.triangles))

        mesh = PolyData(surface.vertices, faces)
        return mesh

    def __toggle_actor(self, change, actor):
        if change.type == 'change':
            if change.new is True:
                self.output_plot.display_actor(actor)
            else:
                self.output_plot.hide_actor(actor)
            self.output_plot.update_plot()

    def __draw_mesh_actor(self, surface, config):
        # type: (Surface, SurfaceWidgetConfig) -> None
        if config is None:
            config = SurfaceWidgetConfig(name='Surface')

        mesh = self.__prepare_mesh(surface)
        mesh_actor = self.output_plot.add_mesh(mesh, config)

        def toggle_surface(change):
            self.__toggle_actor(change, mesh_actor)

        checkbox = ipywidgets.Checkbox(description="Toggle " + config.name, value=True)
        checkbox.observe(toggle_surface, names=['value'])
        self.plot_controls.children += checkbox,
        self.__prepare_surface_controls(mesh_actor, config)

        self.output_plot.update_plot()

    def __draw_connectivity_actor(self, connectivity, config):
        # type: (Connectivity, SurfaceWidgetConfig) -> None
        if config is None:
            config = SurfaceWidgetConfig(color='Green')

        self.output_plot.add_points(connectivity.centres, config)
        self.output_plot.update_plot()

    def __draw_sensors_actor(self, sensors, config):
        # type: (Sensors, SurfaceWidgetConfig) -> None
        if config is None:
            config = SurfaceWidgetConfig(name='Sensors', color='Pink', size=1000)

        sensors_actor = self.output_plot.add_points(sensors.locations, config)

        def toggle_sensors(change):
            self.__toggle_actor(change, sensors_actor)

        checkbox = ipywidgets.Checkbox(description="Toggle " + config.name, value=True)
        checkbox.observe(toggle_sensors, names=['value'])
        self.plot_controls.children += checkbox,

        self.output_plot.update_plot()

    def __prepare_plot_controls(self):
        label = ipywidgets.Label('Display controls: ')
        hbox_checkboxes = ipywidgets.VBox((label,))
        return hbox_checkboxes

    def __prepare_surface_controls(self, actor, config):
        surface_type = ipywidgets.ToggleButtons(options=['Surface', 'Wireframe', 'Points'],
                                                description=config.name + ' controls:', disabled=False)
        surface_type.style.description_width = '150px'

        def toggle_cortex_type(change):
            if change['new'] == 'Wireframe':
                actor.GetProperty().SetRepresentationToWireframe()
            elif change['new'] == 'Surface':
                actor.GetProperty().SetRepresentationToSurface()
            else:
                actor.GetProperty().SetRepresentationToPoints()
            self.output_plot.update_plot()

        surface_type.observe(toggle_cortex_type, 'value')

        surface_opacity = ipywidgets.FloatSlider(value=1, min=0, max=1.0, step=0.1, description='Opacity:',
                                                 disabled=False, continuous_update=False, orientation='horizontal',
                                                 readout=True, readout_format='.1f')

        def on_opacity_change(change):
            value = change['new']
            actor.GetProperty().SetOpacity(value)
            self.output_plot.update_plot()

        surface_opacity.observe(on_opacity_change, names='value')

        hbox_cortex_controls = ipywidgets.HBox([surface_type, surface_opacity])
        self.surface_display_controls.children += hbox_cortex_controls,

# -*- coding: utf-8 -*-
#
# "TheVirtualBrain - Widgets" package
#
# (c) 2022-2023, TVB Widgets Team
#

import ipywidgets
import numpy
import pyvista
from pyvista import PolyData
from tvb.basic.neotraits.api import HasTraits
from tvb.datatypes.connectivity import Connectivity
from tvb.datatypes.region_mapping import RegionMapping
from tvb.datatypes.sensors import Sensors
from tvb.datatypes.surfaces import Surface

from tvbwidgets.ui.base_widget import TVBWidget
from tvbwidgets.ui.widget_with_browser import TVBWidgetWithBrowser

pyvista.set_jupyter_backend('pythreejs')


class HeadWidgetConfig:

    def __init__(self, name='Actor', style='Surface', color='White', light=True, size=1500, cmap=None, scalars=None):
        self.name = name
        self.style = style
        self.color = color
        self.light = light
        self.size = size
        self.cmap = cmap
        self.scalars = scalars
        self.widget = None

    def add_region_mapping_as_cmap(self, region_mapping):
        # type: (RegionMapping) -> None
        self.scalars = region_mapping.array_data
        self.cmap = 'fire'

    def is_incompatible(self, prev_config):
        # type: (HeadWidgetConfig) -> bool
        if prev_config is None:
            return self.cmap is not None
        if (self.cmap is not None and prev_config.cmap is None) or (self.cmap is None and prev_config.cmap is not None):
            return True
        return False


class CustomOutput(ipywidgets.Output):
    CONFIG = HeadWidgetConfig()
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
                                          lighting=config.light, render=False)
        else:
            actor = self.plotter.add_mesh(mesh, name=config.name, style=config.style, scalars=config.scalars,
                                          cmap=config.cmap, lighting=config.light, render=False)
        self.total_actors += 1
        return actor

    def add_points(self, points, config=CONFIG):
        actor = self.plotter.add_points(points, name=config.name, color=config.color,
                                        point_size=config.size, render=False)
        self.total_actors += 1
        return actor

    def display_actor(self, actor):
        self.plotter.renderer.add_actor(actor, render=False)

    def hide_actor(self, actor):
        self.plotter.renderer.remove_actor(actor, render=False)

    def update_plot(self):
        with self:
            self.clear_output(wait=True)
            self.plotter.show()


class ConnectivityWidget(ipywidgets.HBox, TVBWidget):

    def __init__(self, connectivity):
        # type: (Connectivity) -> None
        """
        :param connectivity: Connectivity to view or operate on
        """
        self.connectivity = connectivity
        self.output_plot = CustomOutput()
        self.plot_controls = ipywidgets.Accordion(layout=ipywidgets.Layout(width='380px'))
        self.existent_configs = []

        super().__init__([self.plot_controls, self.output_plot], layout=self.DEFAULT_BORDER)

        self.__draw_connectivity_actor(datatype, config)

    def add_datatype(self, datatype):  # type: (HasTraits) -> None
        pass

    def __toggle_actor(self, change, actor):
        if change.type == 'change':
            if change.new is True:
                self.output_plot.display_actor(actor)
            else:
                self.output_plot.hide_actor(actor)
            self.output_plot.update_plot()

    def __draw_connectivity_actor(self, connectivity, config):
        # type: (Connectivity, HeadWidgetConfig) -> None
        if config is None:
            config = HeadWidgetConfig(name='Connectivity-' + str(connectivity.number_of_regions), color='Green')

        conn_actor = self.output_plot.add_points(connectivity.centres, config)
        controls_vbox = self._prepare_generic_controls(conn_actor, config)
        extra_controls = self.__prepare_points_controls(conn_actor, config)
        controls_vbox.children += extra_controls

        self.plot_controls.children += controls_vbox,
        self.output_plot.update_plot()

    def _prepare_generic_controls(self, actor, config):
        toggle_prefix = "Toggle "
        title_suffix = " Controls"

        idx = self.output_plot.total_actors - 1
        self.plot_controls.set_title(idx, config.name + title_suffix)

        def toggle_actor(change):
            self.__toggle_actor(change, actor)

        toggle_input = ipywidgets.Checkbox(description=toggle_prefix + config.name, value=True)
        toggle_input.observe(toggle_actor, names=['value'])

        def on_name_change(change):
            value = change['new']
            config.name = value
            toggle_input.description = toggle_prefix + config.name
            self.plot_controls.set_title(idx, config.name + title_suffix)

        name_input = ipywidgets.Text(value=config.name, description='Name: ', disabled=False,
                                     layout=ipywidgets.Layout(width='250px'))
        name_input.observe(on_name_change, names='value')

        def on_color_change(change):
            value = change['new']
            rgb = pyvista.Color(value).float_rgb
            actor.GetProperty().SetColor(rgb[0], rgb[1], rgb[2])
            self.output_plot.update_plot()

        color_input = ipywidgets.ColorPicker(concise=False, description='Color: ', value=config.color, disabled=False,
                                             layout=ipywidgets.Layout(width='250px'))
        color_input.observe(on_color_change, names='value')

        controls_vbox = ipywidgets.VBox([toggle_input, name_input, color_input])

        return controls_vbox

    def __prepare_points_controls(self, actor, config):
        def on_size_change(change):
            value = change['new']
            actor.GetProperty().SetPointSize(value)
            self.output_plot.update_plot()

        size_input = ipywidgets.IntText(value=config.size, description='Size: ', disabled=False,
                                        layout=ipywidgets.Layout(width='250px'))
        size_input.observe(on_size_change, names='value')

        return size_input,


class HeadBrowser(ipywidgets.VBox, TVBWidgetWithBrowser):

    def __init__(self):
        super().__init__()
        surface_button = ipywidgets.Button(description='View surface')
        sensors_button = ipywidgets.Button(description='View sensors')
        connectivity_button = ipywidgets.Button(description='View connectivity')
        self.buttons = ipywidgets.HBox([surface_button, sensors_button, connectivity_button],
                                       layout=ipywidgets.Layout(margin="0px 0px 0px 20px"))
        self.head_widget = ConnectivityWidget()
        self.children = [self.storage_widget, self.buttons, self.message_label, self.head_widget]

        def add_surface_datatype(_):
            self.load_selected_file(Surface)

        def add_sensors_datatype(_):
            self.load_selected_file(Sensors, ('.txt', '.txt.bz2'))

        def add_connectivity_datatype(_):
            self.load_selected_file(Connectivity)

        surface_button.on_click(add_surface_datatype)
        sensors_button.on_click(add_sensors_datatype)
        connectivity_button.on_click(add_connectivity_datatype)

    def add_datatype(self, datatype, config=None):
        # type: (HasTraits, HeadWidgetConfig) -> None
        self.head_widget.add_datatype(datatype, config)

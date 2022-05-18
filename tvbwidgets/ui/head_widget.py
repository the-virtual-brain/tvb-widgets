# -*- coding: utf-8 -*-
#
# "TheVirtualBrain - Widgets" package
#
# (c) 2022-2023, TVB Widgets Team
#
import bz2

import ipywidgets
import numpy
import pyvista

from pyvista import PolyData

from tvb.basic.neotraits.api import HasTraits
from tvb.basic.readers import ReaderException
from tvb.datatypes.connectivity import Connectivity
from tvb.datatypes.region_mapping import RegionMapping
from tvb.datatypes.sensors import Sensors
from tvb.datatypes.surfaces import Surface

from tvbwidgets.core.exceptions import InvalidFileException
from tvbwidgets.ui.base_widget import TVBWidget
from tvbwidgets.ui.storage_widget import StorageWidget

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


class HeadWidgetBase(ipywidgets.HBox, TVBWidget):

    def __init__(self, datatypes=None):
        # type: (list[HasTraits]) -> None
        self.output_plot = CustomOutput()
        self.plot_controls = ipywidgets.Accordion(layout=ipywidgets.Layout(width='380px'))

        super().__init__([self.plot_controls, self.output_plot], layout=self.DEFAULT_BORDER)

        if datatypes is not None:
            if not isinstance(datatypes, list):
                self.logger.warning("Input not supported. Please provide a list of datatypes.")
            else:
                for datatype in datatypes:
                    self.add_datatype(datatype)

    def add_datatype(self, datatype, config=None):
        # type: (HasTraits, HeadWidgetConfig) -> None
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
            self.logger.warning(f"Datatype {type(datatype)} not supported by this widget!")

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
        # type: (Surface, HeadWidgetConfig) -> None
        if config is None:
            config = HeadWidgetConfig(name='Surface-' + str(surface.number_of_vertices))

        mesh = self.__prepare_mesh(surface)
        mesh_actor = self.output_plot.add_mesh(mesh, config)

        controls_vbox = self._prepare_generic_controls(mesh_actor, config)

        extra_controls = self.__prepare_surface_controls(mesh_actor)
        controls_vbox.children += extra_controls

        self.plot_controls.children += controls_vbox,
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

    def __draw_sensors_actor(self, sensors, config):
        # type: (Sensors, HeadWidgetConfig) -> None
        if config is None:
            config = HeadWidgetConfig(name='Sensors-' + str(sensors.number_of_sensors), color='Pink', size=1000)

        sensors_actor = self.output_plot.add_points(sensors.locations, config)
        controls_vbox = self._prepare_generic_controls(sensors_actor, config)
        extra_controls = self.__prepare_points_controls(sensors_actor, config)
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

    def __prepare_surface_controls(self, actor):
        surface_type = ipywidgets.ToggleButtons(options=['Surface', 'Wireframe', 'Points'], disabled=False,
                                                layout=ipywidgets.Layout(margin='0px 0px 0px 25px'))
        surface_type.style.button_width = '70px'

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
                                                 readout=True, readout_format='.1f',
                                                 layout=ipywidgets.Layout(width='330px'))

        def on_opacity_change(change):
            value = change['new']
            actor.GetProperty().SetOpacity(value)
            self.output_plot.update_plot()

        surface_opacity.observe(on_opacity_change, names='value')

        return surface_opacity, surface_type

    def __prepare_points_controls(self, actor, config):
        def on_size_change(change):
            value = change['new']
            actor.GetProperty().SetPointSize(value)
            self.output_plot.update_plot()

        size_input = ipywidgets.IntText(value=config.size, description='Size: ', disabled=False,
                                        layout=ipywidgets.Layout(width='250px'))
        size_input.observe(on_size_change, names='value')

        return size_input,


class HeadWidget(ipywidgets.VBox, TVBWidget):
    MSG_TEMPLATE = '<span style="color:{1};">{0}</span>'
    MSG_COLOR = 'red'

    def __init__(self):
        self.storage_widget = StorageWidget()

        surface_button = ipywidgets.Button(description='View surface')
        sensors_button = ipywidgets.Button(description='View sensors')
        connectivity_button = ipywidgets.Button(description='View connectivity')
        self.buttons = ipywidgets.HBox([surface_button, sensors_button, connectivity_button],
                                       layout=ipywidgets.Layout(margin="0px 0px 0px 20px"))
        self.message_label = ipywidgets.HTML(layout=ipywidgets.Layout(height='25px'))
        self.head_widget = HeadWidgetBase()

        super().__init__([self.storage_widget, self.buttons, self.message_label, self.head_widget], **{})

        def add_surface_datatype(_):
            self.__load_selected_file(Surface)

        def add_sensors_datatype(_):
            self.__load_selected_file(Sensors, ('.txt', '.txt.bz2'))

        def add_connectivity_datatype(_):
            self.__load_selected_file(Connectivity)

        surface_button.on_click(add_surface_datatype)
        sensors_button.on_click(add_sensors_datatype)
        connectivity_button.on_click(add_connectivity_datatype)

    def add_datatype(self, datatype, config=None):
        # type: (HasTraits, HeadWidgetConfig) -> None
        self.head_widget.add_datatype(datatype, config)

    def __display_message(self, msg):
        self.message_label.value = self.MSG_TEMPLATE.format(msg, self.MSG_COLOR)

    def __validate_file(self, file_name, accepted_suffix):
        if file_name is None:
            raise InvalidFileException("Please select a file!")

        if not file_name.endswith(accepted_suffix):
            raise InvalidFileException(
                f"Only {' or '.join(ext for ext in accepted_suffix)} files are supported for this data type!")

    def __load_selected_file(self, datatype_cls, accepted_suffix=('.zip',)):
        file_name = self.storage_widget.get_selected_file_name()
        msg = ''

        try:
            self.__validate_file(file_name, accepted_suffix)
        except InvalidFileException as e:
            msg = e.message
            self.logger.error(f"{e}")
            return
        finally:
            self.__display_message(msg)

        content_bytes = self.storage_widget.get_selected_file_content()

        # TODO: this should move inside tvb-library in the next release
        if file_name.endswith('.txt.bz2'):
            decompressor = bz2.BZ2Decompressor()
            content_bytes = decompressor.decompress(content_bytes)

        try:
            datatype = datatype_cls.from_bytes_stream(content_bytes)
            datatype.configure()
            self.add_datatype(datatype)
        except ReaderException as e:
            msg = "The selected file does not contain all necessary data to load this data type! Please check the logs!"
            self.logger.error(f"{e}")
            return
        except Exception as e:
            msg = "Could not load data from this file! Please check the logs!"
            self.logger.error(f"{e}")
            return
        finally:
            self.__display_message(msg)

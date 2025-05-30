# -*- coding: utf-8 -*-
#
# "TheVirtualBrain - Widgets" package
#
# (c) 2022-2025, TVB Widgets Team
#
from dataclasses import dataclass

import ipywidgets
import k3d
import numpy
from tvb.basic.neotraits.api import HasTraits
from tvb.datatypes.connectivity import Connectivity
from tvb.datatypes.region_mapping import RegionMapping
from tvb.datatypes.sensors import Sensors
from tvb.datatypes.surfaces import Surface

from tvbwidgets.core.logger.builder import get_logger
from tvbwidgets.ui.base_widget import TVBWidget
from tvbwidgets.ui.widget_with_browser import TVBWidgetWithBrowser

LOGGER = get_logger(__name__)


@dataclass
class ConnectivityConfig:
    points: str = 'Points'
    edges: str = 'Edges'
    points_color: int = 0x6aa84f  # green
    edge_color: int = 0xfff9f0  # white
    point_size: int = 8
    edge_size: float = 2.5
    point_shader: str = 'dot'
    edge_shader: str = 'simple'
    edge_type: str = 'segment'


@dataclass
class SensorsConfig:
    style: str = 'Points'
    points_color: int = 0xa64d79  # pink
    point_size: int = 3


@dataclass
class SurfaceConfig:
    color: int = 0xefd4d4  # beige
    side_to_draw: str = 'double'
    opacity: float = 0.5


class HeadWidget(ipywidgets.VBox, TVBWidget):

    def __init__(self, datatypes, width=1200, height=550, **kwargs):
        # type: (list[HasTraits], int, int, dict) -> None
        """
        Docs
        """
        self.output = ipywidgets.Output(layout=ipywidgets.Layout(width=str(width) + 'px', height=str(height) + 'px'))
        super(HeadWidget, self).__init__([ipywidgets.HTML(value=f'<h1>{HeadWidget}</h1>'), self.output],
                                         layout=self.DEFAULT_BORDER, *kwargs)
        self.plot = None
        self.refresh_plot(datatypes)

    def __draw_datatypes(self, datatypes):
        if datatypes is not None:
            if not isinstance(datatypes, list):
                self.logger.warning("Input not supported. Please provide a list of datatypes.")
            else:
                for datatype in datatypes:
                    self.add_datatype(datatype)

    def add_datatype(self, datatype, region_mapping=None):
        # type: (HasTraits, RegionMapping) -> None
        if datatype is None:
            self.logger.info("The datatype you have provided is None!")
            return

        if region_mapping and not isinstance(datatype, Surface):
            self.logger.info("A surface is required for displaying the region mapping!!")

        if isinstance(datatype, Surface):
            self.__draw_mesh(datatype, region_mapping)
        elif isinstance(datatype, Connectivity):
            self.__draw_connectivity(datatype)
        elif isinstance(datatype, Sensors):
            self.__draw_sensors(datatype)
        elif isinstance(datatype, RegionMapping):
            self.logger.info(
                "Please provide RegionMapping as a second argument, together with a Surface ad first argument!")
        else:
            self.logger.warning(f"Datatype {type(datatype)} not supported by this widget!")

    def refresh_plot(self, datatypes):
        if self.plot:
            self.plot.close()

        self.plot = k3d.plot(grid_visible=False, background_color=0x999999)
        self.__draw_datatypes(datatypes)

        with self.output:
            self.plot.display()

    def __draw_mesh(self, surface, region_mapping):
        # type: (Surface, RegionMapping) -> None
        color_map = k3d.matplotlib_color_maps.twilight
        mesh_reg_map = []

        if region_mapping:
            if len(region_mapping.array_data) == len(surface.vertices):
                mesh_reg_map = region_mapping.array_data
            else:
                self.logger.info(f"The region mapping should have the same size as the surface vertices!")

        mesh = k3d.mesh(surface.vertices, surface.triangles, side=SurfaceConfig.side_to_draw, color=SurfaceConfig.color,
                        attribute=mesh_reg_map, color_map=color_map, opacity=SurfaceConfig.opacity,
                        name=self.__get_name(surface))

        self.plot += mesh

    def __draw_connectivity(self, connectivity):
        # type: (Connectivity) -> None
        points = k3d.points(connectivity.centres, point_size=ConnectivityConfig.point_size,
                            shader=ConnectivityConfig.point_shader, color=ConnectivityConfig.points_color,
                            name=self.__get_name(connectivity, ConnectivityConfig.points))

        edge_indices = numpy.nonzero(connectivity.weights)
        edges = list(zip(edge_indices[0], edge_indices[1]))

        lines = k3d.lines(connectivity.centres, indices=edges, indices_type=ConnectivityConfig.edge_type,
                          shader=ConnectivityConfig.edge_shader, color=ConnectivityConfig.edge_color,
                          width=ConnectivityConfig.edge_size,
                          name=self.__get_name(connectivity, ConnectivityConfig.edges))

        self.plot += points
        self.plot += lines

    def __draw_sensors(self, sensors):
        # type: (Sensors) -> None
        points = k3d.points(sensors.locations, point_size=SensorsConfig.point_size, color=SensorsConfig.points_color,
                            name=self.__get_name(sensors))
        self.plot += points

    def __get_name(self, datatype, suffix=None):
        if datatype is None:
            return "None"
        if suffix is None:
            suffix = ""

        return datatype.__class__.__name__ + suffix


class HeadBrowser(ipywidgets.VBox, TVBWidgetWithBrowser):

    def __init__(self):
        super().__init__()
        surface_button = ipywidgets.Button(description='View surface')
        sensors_button = ipywidgets.Button(description='View sensors')
        connectivity_button = ipywidgets.Button(description='View connectivity')
        self.buttons = ipywidgets.HBox([surface_button, sensors_button, connectivity_button],
                                       layout=ipywidgets.Layout(margin="0px 0px 0px 20px"))
        self.head_widget = HeadWidget([])
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

    def add_datatype(self, datatype):
        # type: (HasTraits) -> None
        self.head_widget.add_datatype(datatype, None)

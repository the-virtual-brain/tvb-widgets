# -*- coding: utf-8 -*-
#
# "TheVirtualBrain - Widgets" package
#
# (c) 2022-2025, TVB Widgets Team
#

import ipywidgets
import matplotlib
import numpy
import pyvista
import numpy as np
from numpy import ndarray
from tvb.basic.neotraits.api import HasTraits
from tvb.datatypes.connectivity import Connectivity
from tvbwidgets.ui.base_widget import TVBWidget
from tvbwidgets.ui.connectivity_ipy.outputs_3d import PyVistaOutput
from tvbwidgets.ui.connectivity_ipy.operations import ConnectivityOperations
from tvbwidgets.ui.connectivity_ipy.config import ConnectivityConfig
from tvbwidgets.ui.connectivity_ipy.global_context import CONTEXT, ObservableAttrs

DROPDOWN_KEY = 'dropdown'
pyvista.set_jupyter_backend('trame')


class CustomOutput(ipywidgets.Output):
    CONFIG = ConnectivityConfig()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.plotter = matplotlib.pyplot


class Connectivity2DViewer(ipywidgets.VBox, TVBWidget):
    DROPDOWN_DESCRIPTION = 'Matrix:'

    def __init__(self, **kwargs):
        # type: (Connectivity, dict) -> None
        """
        :param connectivity: Connectivity to view or operate on
        """
        self.output = CustomOutput()
        self.widgets_map = dict()

        super().__init__([self.output], **kwargs)

        self.__draw_connectivity()
        self.__show_plot()
        CONTEXT.observe(lambda *args: self.__show_plot(), ObservableAttrs.CONNECTIVITY)

    def add_datatype(self, datatype):  # type: (HasTraits) -> None
        """
        not supported
        """
        pass

    def __show_plot(self, matrix=None):
        # type: (ndarray) -> None
        """
        Clears the custom output and draws the connectivity matrix
        based on the current selection
        """
        dropdown = self.__find_dropdown()
        if not dropdown and matrix is None:
            self.logger.error('No matrix found for plot!')
            return None
        dropdown_matrix = CONTEXT.connectivity.weights if dropdown.value == 'weights' else CONTEXT.connectivity.tract_lengths
        matrix = matrix if matrix is not None else dropdown_matrix
        with self.output:
            self.output.clear_output(wait=True)
            self.output.plotter.figure(figsize=(8, 8))
            heatmap = self.output.plotter.matshow(matrix, fignum=0)
            self.output.plotter.colorbar(heatmap)
            self.output.plotter.show()

    def __find_dropdown(self):
        # type: () -> ipywidgets.Dropdown | None
        try:
            return self.widgets_map[DROPDOWN_KEY]
        except KeyError:
            return None

    def __draw_connectivity(self):
        # type: () -> None
        """
        Creates the connectivity matrix dropdown as a child of this widget
        """

        def on_change(change):
            if change['type'] == 'change' and change['name'] == 'value':
                matrix = CONTEXT.connectivity.weights if change[
                                                             'new'] == 'weights' else CONTEXT.connectivity.tract_lengths
                CONTEXT.matrix = change['new']
                self.__show_plot(matrix)

        dropdown = ipywidgets.Dropdown(
            options=CONTEXT.MATRIX_OPTIONS,
            value=CONTEXT.matrix,
            description='Matrix:'
        )
        dropdown.observe(on_change)

        def on_ctx_change(value):
            dropdown.value = value

        CONTEXT.observe(on_ctx_change, ObservableAttrs.MATRIX)
        self.widgets_map[DROPDOWN_KEY] = dropdown
        self.children = (dropdown, *self.children)


class Connectivity3DViewer(ipywidgets.VBox):

    def __init__(self, width, height, **kwargs):
        self.output = PyVistaOutput()
        self.output.plotter.window_size = [width, height]
        self.output.plotter.set_background("darkgrey")

        super(Connectivity3DViewer, self).__init__([self.output], *kwargs)

        self.__init_view_connectivity()
        CONTEXT.observe(lambda *args: self.__refresh_connectivity(), ObservableAttrs.CONNECTIVITY)

    def __init_view_connectivity(self):
        points, edges = self.__add_actors()
        points_toggle, edges_toggle = self.__init_controls()

        def on_change_points(change):
            if change['new']:
                self.output.display_actor(points)
            else:
                self.output.hide_actor(points)
            self.output.update_plot()

        points_toggle.observe(on_change_points, 'value')

        def on_change_edges(change):
            if change['new']:
                self.output.display_actor(edges)
            else:
                self.output.hide_actor(edges)
            self.output.update_plot()

        edges_toggle.observe(on_change_edges, 'value')

        self.children = [
            ipywidgets.HBox(children=(
                points_toggle, edges_toggle)),
            self.output]
        self.output.display_actor(points)
        self.output.display_actor(edges)
        self.output.update_plot()

    def __refresh_connectivity(self):
        self.output.plotter.clear()
        self.__init_view_connectivity()
        self.output.update_plot()

    def __init_controls(self):
        points_toggle = ipywidgets.ToggleButton(value=True,
                                                description='Points'
                                                )
        edges_toggle = ipywidgets.ToggleButton(value=True,
                                               description='Edges',
                                               )

        return points_toggle, edges_toggle

    def __add_actors(self):
        plotter = self.output.plotter
        points = CONTEXT.connectivity.centres

        mesh_points = pyvista.PolyData(points)

        points_color = self.output.CONFIG.points_color
        points_size = self.output.CONFIG.point_size
        edge_color = self.output.CONFIG.edge_color

        points_actor = plotter.add_points(mesh_points, color=points_color, point_size=points_size)

        edges_coords = self.__extract_edges()
        edges_actor = plotter.add_lines(edges_coords, color=edge_color, width=1)
        plotter.camera_position = 'xy'

        return points_actor, edges_actor

    def __extract_edges(self):
        connectivity = CONTEXT.connectivity
        edge_indices = np.nonzero(connectivity.weights)
        edges = list(zip(edge_indices[0], edge_indices[1]))

        edges_coords = []
        points = connectivity.centres

        for (i, j) in edges:
            edges_coords.append(points[i])
            edges_coords.append(points[j])

        return numpy.array(edges_coords)


class ConnectivityViewers(ipywidgets.Accordion):
    def __init__(self, width, height, **kwargs):
        super().__init__(**kwargs)
        self.children = [
            Connectivity2DViewer(),
            Connectivity3DViewer(width, height)
        ]
        self.set_title(0, '2D Connectivity Matrix viewer')
        self.set_title(1, '3D Connectivity viewer')


class ConnectivityWidget(ipywidgets.VBox, TVBWidget):
    """
    Widget to display a connectivity:
    consists of two tabs, one for connectivity visualizers (2d/3d),
    one for connectivity operations
    :param connectivity: Connectivity to visualize or do operations on
    :param default_active_tab: which tabs are viewable by default ('viewers'|'operations'|'both')
    """

    def add_datatype(self, datatype):
        """
        Doesn't allow this opp. at this time
        """
        pass

    def get_connectivity(self, gid=None):
        # type: (str|None) -> Connectivity
        """
        Get a connectivity with the gid provided from the context history.
        if gid=None return the current connectivity set on CONTEXT
        """
        if gid is None:
            return CONTEXT.connectivity
        conn = list(filter(lambda c: c.gid.hex == gid, CONTEXT.connectivities_history))
        if not len(conn):
            return None
        return conn[0]

    def __init__(self, connectivity, default_active_tab='both', width=500, height=500, **kwargs):

        style = self.DEFAULT_BORDER
        super().__init__(**kwargs, layout=style)

        config = ConnectivityConfig(name=f'Connectivity - {str(connectivity.number_of_regions)}')
        CONTEXT.connectivity = connectivity

        viewers_visible = default_active_tab in ['both', 'viewers']
        operations_visible = default_active_tab in ['both', 'operations']

        self.viewers_tab = ConnectivityViewers(width, height)
        self.viewers_tab.layout.display = viewers_visible and 'inline-block' or 'none'
        self.operations_tab = ConnectivityOperations()
        self.operations_tab.layout.display = operations_visible and 'inline-block' or 'none'
        tabs = (self.viewers_tab, self.operations_tab)

        viewers_checkbox = ipywidgets.Checkbox(value=viewers_visible or default_active_tab == 'viewers',
                                               description='Viewers')

        def on_change_viewers(c):
            self.viewers_tab.layout.display = c['new'] and 'inline-block' or 'none'

        viewers_checkbox.observe(on_change_viewers, 'value')
        operations_checkbox = ipywidgets.Checkbox(
            value=operations_visible, description='Operations')

        def on_change_operations(c):
            self.operations_tab.layout.display = c['new'] and 'inline-block' or 'none'

        operations_checkbox.observe(on_change_operations, 'value')

        sections_container = ipywidgets.HBox(children=tabs)

        children = [
            ipywidgets.VBox(
                children=(
                    ipywidgets.HTML(value=f'<h1>{config.name}</h1>'),
                    ipywidgets.HBox(children=(
                        viewers_checkbox,
                        operations_checkbox
                    )))
            ),
            sections_container
        ]
        self.children = children

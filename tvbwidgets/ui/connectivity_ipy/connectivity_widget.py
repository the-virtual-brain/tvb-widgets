# -*- coding: utf-8 -*-
#
# "TheVirtualBrain - Widgets" package
#
# (c) 2022-2023, TVB Widgets Team
#

import ipywidgets
import matplotlib
import numpy
import pyvista as pv
import numpy as np
from numpy import ndarray
from tvb.basic.neotraits.api import HasTraits
from tvb.datatypes.connectivity import Connectivity
from tvbwidgets.ui.base_widget import TVBWidget
from tvbwidgets.ui.connectivity_ipy.outputs_3d import PyVistaOutput
from tvbwidgets.ui.connectivity_ipy.operations import ConnectivityOperations
from tvbwidgets.ui.connectivity_ipy.config import ConnectivityConfig
from tvbwidgets.ui.connectivity_ipy.global_context import CONTEXT

DROPDOWN_KEY = 'dropdown'


class CustomOutput(ipywidgets.Output):
    CONFIG = ConnectivityConfig()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.plotter = matplotlib.pyplot


class Connectivity2DViewer(ipywidgets.VBox, TVBWidget):
    DROPDOWN_DESCRIPTION = 'Matrix:'

    def __init__(self, connectivity, **kwargs):
        # type: (Connectivity, dict) -> None
        """
        :param connectivity: Connectivity to view or operate on
        """
        self.connectivity = connectivity
        self.output = CustomOutput()
        self.widgets_map = dict()

        super().__init__([self.output], **kwargs)

        self.__draw_connectivity()
        self.__show_plot()

    def add_datatype(self, datatype):  # type: (HasTraits) -> None
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
        dropdown_matrix = self.connectivity.weights if dropdown.value == 'weights' else self.connectivity.tract_lengths
        matrix = matrix if matrix is not None else dropdown_matrix
        with self.output:
            self.output.clear_output(wait=True)
            self.output.plotter.figure(figsize=(8, 8))
            heatmap = self.output.plotter.matshow(matrix, fignum=1)
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
                matrix = self.connectivity.weights if change['new'] == 'weights' else self.connectivity.tract_lengths
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

        CONTEXT.observe(on_ctx_change, 'matrix')
        self.widgets_map[DROPDOWN_KEY] = dropdown
        self.children = (dropdown, *self.children)


class Connectivity3DViewer(ipywidgets.VBox):
    PYVISTA = 'PyVista'

    def __init__(self, connectivity, **kwargs):
        self.connectivity = connectivity

        self.output = PyVistaOutput()

        super(Connectivity3DViewer, self).__init__([self.output], *kwargs)

        self.init_view_connectivity()

    def init_view_connectivity(self):
        points, edges, labels = self.add_actors()
        points_toggle, edges_toggle, labels_toggle = self._init_controls()
        if not labels_toggle.value:
            self.output.hide_actor(labels)

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

        def on_change_labels(change):
            if change['new']:
                self.output.display_actor(labels)
            else:
                self.output.hide_actor(labels)
            self.output.update_plot()

        labels_toggle.observe(on_change_labels, 'value')

        window_controls = self.output.get_window_controls()

        self.children = [
            ipywidgets.HBox(children=(
                points_toggle, edges_toggle, labels_toggle)),
            window_controls,
            self.output]
        self.output.display_actor(points)
        self.output.display_actor(edges)
        self.output.update_plot()

    def _init_controls(self):
        points_toggle = ipywidgets.ToggleButton(value=True,
                                                description='Points'
                                                )
        edges_toggle = ipywidgets.ToggleButton(value=True,
                                               description='Edges',
                                               )

        labels_toggle = ipywidgets.ToggleButton(value=False,
                                                description='Labels')
        return points_toggle, edges_toggle, labels_toggle

    def add_actors(self):
        plotter = self.output.plotter
        points = self.connectivity.centres

        mesh_points = pv.PolyData(points)

        labels = self.connectivity.region_labels
        labels_actor = plotter.add_point_labels(points, labels)

        points_color = self.output.CONFIG.points_color
        points_size = self.output.CONFIG.point_size
        edge_color = self.output.CONFIG.edge_color

        points_actor = plotter.add_points(mesh_points, color=points_color, point_size=points_size)

        edges_coords = self._extract_edges()

        edges_actor = plotter.add_lines(edges_coords, color=edge_color, width=1)
        plotter.camera_position = 'xy'

        return points_actor, edges_actor, labels_actor

    def _extract_edges(self):
        connectivity = self.connectivity
        edge_indices = np.nonzero(connectivity.weights)
        edges = list(zip(edge_indices[0], edge_indices[1]))

        edges_coords = []
        points = connectivity.centres

        for (i, j) in edges:
            edges_coords.append(points[i])
            edges_coords.append(points[j])

        return numpy.array(edges_coords)


class ConnectivityViewers(ipywidgets.Accordion):
    def __init__(self, connectivity, **kwargs):
        super().__init__(**kwargs)
        self.children = [
            Connectivity2DViewer(connectivity),
            Connectivity3DViewer(connectivity)
        ]
        self.set_title(0, '2D Connectivity Matrix viewer')
        self.set_title(1, '3D Connectivity viewer')


class ConnectivityWidget(ipywidgets.VBox, TVBWidget):
    def add_datatype(self, datatype):
        """
        Doesn't allow this opp. at this time
        """
        pass

    def __init__(self, connectivity, **kwargs):
        style = self.DEFAULT_BORDER
        super().__init__(**kwargs, layout=style)

        config = ConnectivityConfig(name=f'Connectivity - {str(connectivity.number_of_regions)}')

        self.viewers_tab = ConnectivityViewers(connectivity)
        self.operations_tab = ConnectivityOperations(connectivity)
        tabs = (self.viewers_tab, self.operations_tab)

        viewers_checkbox = ipywidgets.Checkbox(value=True, description='Viewers')

        def on_change_viewers(c):
            self.viewers_tab.layout.display = c['new'] and 'inline-block' or 'none'

        viewers_checkbox.observe(on_change_viewers, 'value')
        operations_checkbox = ipywidgets.Checkbox(value=True, description='Operations')

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
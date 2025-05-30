# -*- coding: utf-8 -*-
#
# "TheVirtualBrain - Widgets" package
#
# (c) 2022-2025, TVB Widgets Team
#

import ipywidgets
import matplotlib
from numpy import ndarray
from tvb.basic.neotraits.api import HasTraits
from tvb.datatypes.connectivity import Connectivity
from tvbwidgets.ui.base_widget import TVBWidget
from tvbwidgets.ui.connectivity_ipy.operations import ConnectivityOperations
from tvbwidgets.ui.connectivity_ipy.global_context import CONTEXT, ObservableAttrs
from tvbwidgets.ui.head_widget import HeadWidget

DROPDOWN_KEY = 'dropdown'


class CustomOutput(ipywidgets.Output):

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


class ConnectivityViewers(ipywidgets.Accordion):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        head_widget = HeadWidget([CONTEXT.connectivity], 600, 550)
        CONTEXT.observe(lambda *args: head_widget.refresh_plot([CONTEXT.connectivity]), ObservableAttrs.CONNECTIVITY)

        self.children = [
            Connectivity2DViewer(),
            head_widget
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

    def __init__(self, connectivity, default_active_tab='both', **kwargs):

        style = self.DEFAULT_BORDER
        super().__init__(**kwargs, layout=style)

        CONTEXT.connectivity = connectivity

        viewers_visible = default_active_tab in ['both', 'viewers']
        operations_visible = default_active_tab in ['both', 'operations']

        self.viewers_tab = ConnectivityViewers()
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

        connectivity_name = f'Connectivity - {str(connectivity.number_of_regions)}'
        children = [
            ipywidgets.VBox(
                children=(
                    ipywidgets.HTML(value=f'<h1>{connectivity_name}</h1>'),
                    ipywidgets.HBox(children=(
                        viewers_checkbox,
                        operations_checkbox
                    )))
            ),
            sections_container
        ]
        self.children = children

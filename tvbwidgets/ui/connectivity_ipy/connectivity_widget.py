# -*- coding: utf-8 -*-
#
# "TheVirtualBrain - Widgets" package
#
# (c) 2022-2023, TVB Widgets Team
#
import dataclasses

import ipywidgets
import pyvista
import matplotlib
from numpy import ndarray
from tvb.basic.neotraits._attr import NArray
from tvb.basic.neotraits.api import HasTraits
from tvb.datatypes.connectivity import Connectivity
from tvbwidgets.ui.base_widget import TVBWidget

pyvista.set_jupyter_backend('pythreejs')

DROPDOWN_KEY = 'dropdown'


@dataclasses.dataclass
class ConnectivityConfig:
    name: str = 'Connectivity'
    style: str = 'Surface'
    color: str = 'White'
    light: bool = True
    size: int = 1500
    cmap: str | None = None
    scalars: ndarray | NArray = None
    widget: ipywidgets.Widget = None


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
            self.output.plotter.matshow(matrix)
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
                self.__show_plot(matrix)

        dropdown = ipywidgets.Dropdown(
            options=[('Tracts', 'tracts'), ('Weights', 'weights')],
            value='weights',
            description='Matrix:'
        )
        dropdown.observe(on_change)
        self.widgets_map[DROPDOWN_KEY] = dropdown
        self.children = (dropdown, *self.children)


class Connectivity3DViewer(ipywidgets.HBox):
    def __init__(self, connectivity, **kwargs):
        super(Connectivity3DViewer, self).__init__(*kwargs)
        self.children = [ipywidgets.HTML(value='Placeholder for 3d viewer')]


class ConnectivityOperations(ipywidgets.VBox, TVBWidget):
    def add_datatype(self, datatype):
        """
        Currently not supported
        """
        pass

    def __init__(self, connectivity, **kwargs):
        super().__init__(layout=self.DEFAULT_BORDER, **kwargs)
        children = [
            ipywidgets.HTML(
                value=f'Placeholder text for operations on Connectivity-{connectivity.number_of_regions}'
            )]
        self.children = children


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
            ipywidgets.HBox(
                children=(
                    ipywidgets.HTML(value=f'<h1>{config.name}</h1>'),
                    ipywidgets.VBox(children=(
                        viewers_checkbox,
                        operations_checkbox
                    )
                    )

                )
            ),
            sections_container
        ]
        self.children = children

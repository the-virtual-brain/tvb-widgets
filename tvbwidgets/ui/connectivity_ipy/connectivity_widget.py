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
    MAX_ACTORS = 10

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.plotter = matplotlib.pyplot


class ConnectivityWidget(ipywidgets.HBox, TVBWidget):
    DROPDOWN_DESCRIPTION = 'Matrix:'

    def __init__(self, connectivity):
        # type: (Connectivity) -> None
        """
        :param connectivity: Connectivity to view or operate on
        """
        self.connectivity = connectivity
        self.output_plot = CustomOutput()

        super().__init__([self.output_plot], layout=self.DEFAULT_BORDER)

        self.__draw_connectivity()

    def add_datatype(self, datatype):  # type: (HasTraits) -> None
        pass

    def __show_plot(self, matrix=None):
        dropdown = self.__find_dropdown()
        if not dropdown and matrix is None:
            self.logger.error('Non matrix found for plot!')
            return None
        dropdown_matrix = self.connectivity.weights if dropdown.value == 'weights' else self.connectivity.tract_lengths
        matrix = matrix if matrix is not None else dropdown_matrix
        with self.output_plot:
            self.output_plot.clear_output(wait=True)
            self.output_plot.plotter.matshow(matrix)
            self.output_plot.plotter.show()

    def __find_dropdown(self):
        # type: () -> ipywidgets.Dropdown | None
        for wid in self.children:
            try:
                if wid.description and wid.description == self.DROPDOWN_DESCRIPTION:
                    return wid
            except AttributeError:
                pass
        return None

    def __draw_connectivity(self):
        # type: () -> None
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
        self.children = (dropdown, *self.children)
        self.__show_plot()

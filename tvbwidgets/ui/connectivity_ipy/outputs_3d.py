# -*- coding: utf-8 -*-
#
# "TheVirtualBrain - Widgets" package
#
# (c) 2022-2025, TVB Widgets Team
#

from tvbwidgets.ui.connectivity_ipy.config import ConnectivityConfig
from tvbwidgets.ui.connectivity_ipy.exceptions import UnknownOutputException
from enum import Enum
import ipywidgets as widgets
import pyvista
from tvbwidgets.core.logger.builder import get_logger

LOGGER = get_logger(__name__)


class Output3D(Enum):
    PYVISTA = 'PyVista'

    def __str__(self):
        return str(self.value)


class PyVistaOutput(widgets.Output):
    CONFIG = ConnectivityConfig()
    plotter = pyvista.Plotter()

    def toggle_actor(self, actor, visible):
        if visible:
            self.display_actor(actor)
        else:
            self.hide_actor(actor)
        self.update_plot()

    def display_actor(self, actor):
        self.plotter.renderer.add_actor(actor, render=False)

    def hide_actor(self, actor):
        self.plotter.renderer.remove_actor(actor, render=False)

    def update_plot(self):
        with self:
            LOGGER.info("update plot")
            self.clear_output(wait=True)
            self.plotter.show()


def output_3d_factory(output_type):
    """Factory function for a custom 3d output"""
    if output_type == Output3D.PYVISTA:
        return PyVistaOutput()
    raise UnknownOutputException(f"No applicable output for {output_type}!")


import numpy as np
import ipywidgets as widgets
import k3d

from tvbwidgets.ui.head_widget import HeadWidget
from tvbwidgets.ui.connectivity_matrix_editor_widget import ConnectivityMatrixEditor

class BCTConnectivityMatrixEditor(ConnectivityMatrixEditor):
    """ConnectivityMatrixEditor stripped to weights tab only."""

    def __init__(self, connectivity, **kwargs):
        super().__init__(connectivity, **kwargs)
        self.tab.children = [self.tab.children[0]]
        self.tab.set_title(0, "weights")

class BCTTractLengthsMatrixEditor(ConnectivityMatrixEditor):
    """ConnectivityMatrixEditor stripped to tract_lengths tab only.
    """

    def __init__(self, connectivity, **kwargs):
        super().__init__(connectivity, **kwargs)
        self.tab.children = [self.tab.children[1]]
        self.tab.set_title(0, "tract_lengths")

class ColoredConnectivityHeadWidget(HeadWidget):
    """HeadWidget with per-node coloring driven by BCT metric values."""

    def __init__(self, datatypes, node_values=None, region_labels=None, **kwargs):
        self.node_values = node_values
        self.region_labels = region_labels
        super().__init__(datatypes, **kwargs)

    def _HeadWidget__draw_connectivity(self, connectivity):
        self._centres = connectivity.centres
        self._labels = (
            self.region_labels if self.region_labels is not None
            else connectivity.region_labels
        )

        values = self.node_values if self.node_values is not None else np.ones(len(connectivity.centres))
        values = np.array(values, dtype=float)
        values[np.isinf(values)] = 0
        values[np.isnan(values)] = 0
        self._values = values

        vmin, vmax = float(values.min()), float(values.max())
        if vmin == vmax:
            vmin -= 0.5
            vmax += 0.5

        self._points_obj = k3d.points(
            connectivity.centres,
            point_size=8,
            shader='dot',
            attribute=values,
            color_map=k3d.matplotlib_color_maps.viridis,
            color_range=[vmin, vmax],
        )

        edge_indices = np.nonzero(connectivity.weights)
        edges = list(zip(edge_indices[0], edge_indices[1]))
        lines = k3d.lines(
            connectivity.centres,
            indices=edges,
            shader='simple',
            color=0xffffff,
            width=2,
        )

        self.plot += self._points_obj
        self.plot += lines

    def display(self):
        pass
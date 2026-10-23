import k3d
import numpy

from tvbwidgets.ui.head_widget import HeadWidget, ConnectivityConfig

UNSELECTED_NODE_COLOR = 0xffffff
NODE_EDGE_COLORS = (0xff8800, 0x2196f3, 0xe53935, 0x8e24aa, 0xfdd835, 0x00bcd4, 0xec407a, 0x8d6e63)
NODE_HIGHLIGHT_EDGE_WIDTH_MULTIPLIER = 1.8


class _SelectableHeadWidget(HeadWidget):

    def __init__(self, *args, **kwargs):
        self._node_edge_objects = {}
        super().__init__(*args, **kwargs)

    def _find_points_object(self, connectivity):
        target_name = connectivity.__class__.__name__ + ConnectivityConfig.points
        for obj in self.plot.objects:
            if getattr(obj, "name", None) == target_name:
                return obj
        return None

    def _find_lines_object(self, connectivity):
        target_name = connectivity.__class__.__name__ + ConnectivityConfig.edges
        for obj in self.plot.objects:
            if getattr(obj, "name", None) == target_name:
                return obj
        return None

    def set_node_selection(self, connectivity, selected_mask):
        points = self._find_points_object(connectivity)
        if points is None:
            self.logger.warning(
                "No connectivity points found for gid %s - draw it before selecting nodes."
                % connectivity.gid.hex)
            return

        mask = numpy.asarray(list(selected_mask), dtype=bool)
        if len(mask) != len(connectivity.centres):
            self.logger.warning(
                "Selection length (%d) does not match number of connectivity nodes (%d)."
                % (len(mask), len(connectivity.centres)))
            return

        colors = numpy.where(mask, numpy.uint32(ConnectivityConfig.points_color),
                             numpy.uint32(UNSELECTED_NODE_COLOR))
        with points.hold_sync():
            # k3d multiplies each node color by color, so color is white to keep the node colors unchanged
            points.color = UNSELECTED_NODE_COLOR
            points.colors = colors.astype(numpy.uint32)

    def refresh_edges(self, connectivity, weights):
        self._keep_camera()
        lines = self._find_lines_object(connectivity)
        if lines is None:
            self.logger.warning(
                "No connectivity edges found for gid %s - draw it before refreshing edges."
                % connectivity.gid.hex)
            return

        edge_indices = numpy.nonzero(weights)
        lines.indices = numpy.array(list(zip(edge_indices[0], edge_indices[1])), dtype=numpy.uint32).reshape(-1, 2)

    def show_node_edges(self, connectivity, edges_by_node):
        self._keep_camera()
        removed = [node for node in self._node_edge_objects if node not in edges_by_node]
        for node in removed:
            self.plot -= self._node_edge_objects.pop(node)

        for node, edges in edges_by_node.items():
            indices = numpy.array(edges, dtype=numpy.uint32)
            lines = self._node_edge_objects.get(node)
            if lines is not None:
                lines.indices = indices
                continue

            used = [obj.color for obj in self._node_edge_objects.values()]
            free = [color for color in NODE_EDGE_COLORS if color not in used]
            color = free[0] if free else NODE_EDGE_COLORS[len(used) % len(NODE_EDGE_COLORS)]
            lines = k3d.lines(connectivity.centres, indices=indices,
                              indices_type=ConnectivityConfig.edge_type,
                              shader=ConnectivityConfig.edge_shader, color=color,
                              width=ConnectivityConfig.edge_size * NODE_HIGHLIGHT_EDGE_WIDTH_MULTIPLIER,
                              name="{} edges".format(connectivity.region_labels[node]))
            self._node_edge_objects[node] = lines
            self.plot += lines

    def _keep_camera(self):
        self.plot.camera_auto_fit = False
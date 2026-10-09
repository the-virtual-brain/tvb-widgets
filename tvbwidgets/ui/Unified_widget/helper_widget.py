import k3d
import numpy

from tvbwidgets.ui.head_widget import HeadWidget, ConnectivityConfig

UNSELECTED_NODE_COLOR = 0xffffff
NODE_OUTGOING_COLOR = 0xff8800
NODE_INCOMING_COLOR = 0x2196f3
NODE_HIGHLIGHT_EDGE_WIDTH_MULTIPLIER = 1.8


class _SelectableHeadWidget(HeadWidget):

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
        points.colors = colors.astype(numpy.uint32)

    def refresh_edges(self, connectivity, weights):
        old_lines = self._find_lines_object(connectivity)
        if old_lines is None:
            self.logger.warning(
                "No connectivity edges found for gid %s - draw it before refreshing edges."
                % connectivity.gid.hex)
            return

        edge_indices = numpy.nonzero(weights)
        edges = list(zip(edge_indices[0], edge_indices[1]))

        new_lines = k3d.lines(connectivity.centres, indices=edges,
                              indices_type=ConnectivityConfig.edge_type,
                              shader=ConnectivityConfig.edge_shader,
                              color=ConnectivityConfig.edge_color,
                              width=ConnectivityConfig.edge_size,
                              name=old_lines.name)

        self.plot -= old_lines
        self.plot += new_lines

    def _find_node_highlight_object(self, connectivity):
        target_name = connectivity.__class__.__name__ + ConnectivityConfig.edges + "Highlight"
        for obj in self.plot.objects:
            if getattr(obj, "name", None) == target_name:
                return obj
        return None

    def highlight_node_edges(self, connectivity, node_index, direction):
        existing = self._find_node_highlight_object(connectivity)
        if existing is not None:
            self.plot -= existing

        if direction is None:
            return

        weights = connectivity.weights
        if direction == "outgoing":
            others = numpy.nonzero(weights[node_index, :])[0]
            pairs = [(node_index, j) for j in others if j != node_index]
            color = NODE_OUTGOING_COLOR
        elif direction == "incoming":
            others = numpy.nonzero(weights[:, node_index])[0]
            pairs = [(i, node_index) for i in others if i != node_index]
            color = NODE_INCOMING_COLOR
        else:
            self.logger.warning("highlight_node_edges: unknown direction '%s'." % direction)
            return

        if not pairs:
            self.logger.info(
                "highlight_node_edges: node %d has no %s connections." % (node_index, direction))
            return

        vertices = []
        indices = []
        for a, b in pairs:
            vertices.append(connectivity.centres[a])
            vertices.append(connectivity.centres[b])
            start = len(vertices) - 2
            indices.append((start, start + 1))

        highlight_lines = k3d.lines(numpy.array(vertices), indices=indices,
                                    indices_type=ConnectivityConfig.edge_type,
                                    shader=ConnectivityConfig.edge_shader, color=color,
                                    width=ConnectivityConfig.edge_size * NODE_HIGHLIGHT_EDGE_WIDTH_MULTIPLIER,
                                    name=connectivity.__class__.__name__ + ConnectivityConfig.edges + "Highlight")
        self.plot += highlight_lines
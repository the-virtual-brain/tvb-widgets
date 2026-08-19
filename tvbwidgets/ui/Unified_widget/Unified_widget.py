import numpy
import ipycanvas as canvas
import ipywidgets as widgets
from tvb.datatypes.connectivity import Connectivity

from tvbwidgets.core.logger.builder import get_logger
from tvbwidgets.ui.base_widget import TVBWidget
from tvbwidgets.ui.connectivity_matrix_editor_widget import ConnectivityMatrixEditor
from tvbwidgets.ui.spacetime_widget import SpaceTimeVisualizerWidget
from .helper_widget import _SelectableHeadWidget
from .style import _STYLE

LOGGER = get_logger(__name__)

NEW_SELECTION_OPTION = "New selection"
NODE_CHECKBOX_COLUMNS = 4
EDITED_CELL_OUTLINE_COLOR = "#ff8800"
EDITED_CELL_OUTLINE_WIDTH = 2


class LargeScaleConnectivityWidget(widgets.VBox, TVBWidget):

    def __init__(self, connectivity, view_width=None, view_height=None,
                 matrix_size=None, **kwargs):
        super().__init__(**kwargs)

        self.connectivity = connectivity

        head_widget_kwargs = {}
        if view_width is not None:
            head_widget_kwargs["width"] = view_width
        if view_height is not None:
            head_widget_kwargs["height"] = view_height

        self.head_widget = _SelectableHeadWidget([connectivity], **head_widget_kwargs)
        self.head_widget.children = self.head_widget.children[1:]
        matrix_editor_kwargs = {}
        if matrix_size is not None:
            matrix_editor_kwargs["size"] = matrix_size

        self.matrix_editor = ConnectivityMatrixEditor(connectivity, **matrix_editor_kwargs)
        self._unclip_matrix_scroll_containers()
        self.matrix_editor.save_button.on_click(self._on_matrix_editor_saved)
        self.matrix_editor.quadrants.observe(self._on_matrix_quadrant_changed, names="value")

        self._node_selections = {}
        self._node_checkboxes = {}
        self._active_node_mask = [True] * len(connectivity.region_labels)

        self._last_edited_rows = []
        self._last_edited_cols = []

        head_view_tab = self._build_head_view_tab()
        space_time_tab = self._build_space_time_tab()
        control_tab = self._build_matrix_tab()

        self.view_subtabs = widgets.Tab(children=[head_view_tab, space_time_tab])
        self.view_subtabs.set_title(0, "Head View")
        self.view_subtabs.set_title(1, "Space Time")

        self.tabs = widgets.Tab(children=[self.view_subtabs, control_tab])
        self.tabs.set_title(0, "VIEW")
        self.tabs.set_title(1, "CONTROL")

        for tab_widget in (self.tabs, self.view_subtabs, self.matrix_editor.tab):
            tab_widget.layout.overflow = "visible"
            tab_widget.layout.height = "auto"

        self.children = [
            widgets.HTML(_STYLE),
            self.tabs,
        ]

        self.add_class("lsc-wrapper")

    def _build_head_view_tab(self):
        node_control_bar = self._build_node_control_bar()

        head_container = widgets.Box(
            [self.head_widget],
            layout=widgets.Layout(
                width="100%",
                display="flex",
                flex_flow="column",
                align_items="center",
            ),
        )

        panel = widgets.VBox(
            [node_control_bar, head_container],
            layout=widgets.Layout(width="100%", align_items="center"),
        )
        panel.add_class("lsc-panel")
        return panel

    def _unclip_matrix_scroll_containers(self):
        try:
            for tab_child in self.matrix_editor.tab.children:
                inner_container = tab_child.children[0]
                inner_container.layout.height = "auto"
                inner_container.layout.max_height = "none"
                inner_container.layout.overflow_y = "visible"
        except (AttributeError, IndexError) as exc:
            LOGGER.warning("Could not unclip matrix editor scroll containers: %s" % exc)

    def _build_node_control_bar(self):
        self.node_dropdown = widgets.Dropdown(
            options=[(str(label), idx) for idx, label in enumerate(self.connectivity.region_labels)],
            description="Node:",
            layout=widgets.Layout(width="260px"),
        )

        incoming_button = widgets.Button(description="Incoming", layout=widgets.Layout(width="100px"))
        outgoing_button = widgets.Button(description="Outgoing", layout=widgets.Layout(width="100px"))
        clear_button = widgets.Button(description="Clear", layout=widgets.Layout(width="90px"))
        incoming_button.on_click(lambda _: self._on_node_direction_click("incoming"))
        outgoing_button.on_click(lambda _: self._on_node_direction_click("outgoing"))
        clear_button.on_click(lambda _: self._on_node_direction_click(None))

        bar = widgets.HBox(
            [self.node_dropdown, incoming_button, outgoing_button, clear_button],
            layout=widgets.Layout(align_items="center", gap="8px", width="100%"),
        )
        bar.add_class("lsc-selection-bar")
        return bar

    def _on_node_direction_click(self, direction):
        self.head_widget.highlight_node_edges(self.matrix_editor.new_connectivity, self.node_dropdown.value, direction)

    def _build_space_time_tab(self):
        self.space_time_container = widgets.VBox(layout=widgets.Layout(width="100%"))
        self._rebuild_space_time_widget(self.connectivity)

        body = widgets.Box(
            [self.space_time_container],
            layout=widgets.Layout(width="100%"),
        )
        body.add_class("lsc-tab-body")

        panel = widgets.Box(
            [body],
            layout=widgets.Layout(width="100%"),
        )
        panel.add_class("lsc-panel")
        return panel

    def _rebuild_space_time_widget(self, connectivity):
        space_time_widget = SpaceTimeVisualizerWidget(connectivity)
        space_time_widget.plot.mode = 'callback'

        self.space_time_widget = space_time_widget
        self.space_time_container.children = [space_time_widget.options, space_time_widget.hbox]

    def _on_matrix_editor_saved(self, change):
        self._last_edited_rows, self._last_edited_cols = [], []
        self._rebuild_space_time_widget(self.matrix_editor.connectivity)

    def _build_matrix_tab(self):
        selection_label = widgets.HTML(
            '<span class="lsc-selection-label">Selection:</span>'
        )

        edge_button = widgets.Button(description="Edge Operations")
        select_button = widgets.Button(description="Select Nodes")
        reset_button = widgets.Button(description="Reset Edits", icon="undo")

        edge_button.on_click(self._on_edge_operations_click)
        select_button.on_click(self._on_select_nodes_click)
        reset_button.on_click(self._on_reset_edits_click)

        selection_bar = widgets.HBox(
            [selection_label, edge_button, select_button, reset_button],
            layout=widgets.Layout(
                align_items="center",
                gap="8px",
                width="100%",
            ),
        )
        selection_bar.add_class("lsc-selection-bar")

        self.select_nodes_popup = self._build_select_nodes_popup()
        self.edge_operations_popup = self._build_edge_operations_popup()

        matrix_body = widgets.VBox(
            [self.matrix_editor.header, self.matrix_editor.tab, self.edge_operations_popup, self.select_nodes_popup],
            layout=widgets.Layout(width="100%", position="relative", overflow="visible"),
        )
        matrix_body.add_class("lsc-tab-body")

        content = widgets.VBox(
            [selection_bar, matrix_body],
            layout=widgets.Layout(width="100%"),
        )

        panel = widgets.Box(
            [content],
            layout=widgets.Layout(width="100%", position="relative", overflow="visible"),
        )
        panel.add_class("lsc-panel")
        return panel

    def _build_edge_operations_popup(self):
        title = widgets.HTML('<div class="lsc-select-nodes-title">Edge Operations</div>')

        close_button = widgets.Button(description="\u2715", layout=widgets.Layout(width="32px"))
        close_button.add_class("lsc-select-nodes-close")
        close_button.on_click(lambda _: self._set_edge_operations_popup_visible(False))

        title_row = widgets.HBox(
            [title, close_button],
            layout=widgets.Layout(justify_content="space-between", align_items="center", width="100%"),
        )

        operation_label = widgets.HTML('<div class="lsc-edge-op-label">Operation</div>')
        self.operation_dropdown = widgets.Dropdown(
            options=[("Set(n)", "Set"), ("Add", "Add"), ("Subtract", "Subtract"),
                     ("Multiply", "Multiply"), ("Divide", "Divide")],
            value="Set",
            layout=widgets.Layout(width="100%"),
        )

        edge_type_label = widgets.HTML('<div class="lsc-edge-op-label">Edges type</div>')
        self.edge_type_dropdown = widgets.Dropdown(
            options=["In -> In", "In -> Out", "Out -> In", "Out -> Out"],
            value="In -> In",
            layout=widgets.Layout(width="100%"),
        )

        weight_label = widgets.HTML('<div class="lsc-edge-op-label">Weight change</div>')
        self.weight_change_input = widgets.Text(value="0.5", layout=widgets.Layout(width="100%"))

        apply_button = widgets.Button(
            description="Apply weight change",
            icon="cog",
            layout=widgets.Layout(width="100%", margin="12px 0 0 0"),
        )
        apply_button.add_class("lsc-btn")
        apply_button.on_click(self._on_apply_edge_operation)

        self.edge_operation_error_label = widgets.HTML(
            value="", layout=widgets.Layout(margin="6px 0 0 0"))

        popup = widgets.VBox(
            [title_row, operation_label, self.operation_dropdown,
             edge_type_label, self.edge_type_dropdown,
             weight_label, self.weight_change_input,
             apply_button, self.edge_operation_error_label],
            layout=widgets.Layout(
                position="absolute",
                top="72px",
                left="140px",
                width="300px",
                z_index="20",
                visibility="hidden",
            ),
        )
        popup.add_class("lsc-edge-operations-popup")
        return popup

    def _set_edge_operations_popup_visible(self, visible):
        self.edge_operations_popup.layout.visibility = "visible" if visible else "hidden"

    def _set_edge_operation_error(self, message):
        if message:
            self.edge_operation_error_label.value = (
                '<span style="color:#d32f2f;font-size:11px;">{}</span>'.format(message))
        else:
            self.edge_operation_error_label.value = ""

    def _on_apply_edge_operation(self, change):
        self._set_edge_operation_error("")

        try:
            value = float(self.weight_change_input.value)
        except (TypeError, ValueError):
            self._set_edge_operation_error("Weight change must be a number.")
            LOGGER.warning(
                "Edge Operations: '%s' is not a valid numeric weight change." % self.weight_change_input.value)
            return

        operation = self.operation_dropdown.value
        edge_type = self.edge_type_dropdown.value

        selected = [i for i, is_in in enumerate(self._active_node_mask) if is_in]
        unselected = [i for i, is_in in enumerate(self._active_node_mask) if not is_in]

        if edge_type == "In -> In":
            rows, cols = selected, selected
        elif edge_type == "In -> Out":
            rows, cols = selected, unselected
        elif edge_type == "Out -> In":
            rows, cols = unselected, selected
        else:
            rows, cols = unselected, unselected

        if not rows or not cols:
            LOGGER.info("Edge Operations: '%s' set is empty for the current node selection - nothing to apply."
                        % edge_type)
            return

        if operation == "Divide" and value == 0:
            self._set_edge_operation_error("Division by zero is not possible.")
            LOGGER.warning("Edge Operations: cannot divide by zero.")
            return

        weights = self.matrix_editor.new_connectivity.weights
        idx = numpy.ix_(rows, cols)
        current = weights[idx]

        if operation == "Set":
            new_values = numpy.full_like(current, value)
        elif operation == "Add":
            new_values = current + value
        elif operation == "Subtract":
            new_values = current - value
        elif operation == "Multiply":
            new_values = current * value
        elif operation == "Divide":
            new_values = current / value

        weights[idx] = numpy.clip(new_values, 0, None)

        self.matrix_editor.is_connectivity_being_edited = True
        self.matrix_editor._update_matrices_view(self.matrix_editor.new_connectivity)

        self._last_edited_rows, self._last_edited_cols = rows, cols
        self._highlight_edited_cells(rows, cols)

        self.head_widget.refresh_edges(self.matrix_editor.new_connectivity, weights)

    def _highlight_edited_cells(self, rows, cols):
        editor = self.matrix_editor
        weights_canvas = editor.weights_matrix
        from_row, from_col, num_rows = editor.from_row, editor.from_col, editor.num_rows
        cell_size, offset = editor.cell_size, editor.layout_offset

        visible_rows = [r for r in rows if from_row <= r < from_row + num_rows]
        visible_cols = [c for c in cols if from_col <= c < from_col + num_rows]
        if not visible_rows or not visible_cols:
            return

        with canvas.hold_canvas(weights_canvas[5]):
            weights_canvas[5].line_width = EDITED_CELL_OUTLINE_WIDTH
            weights_canvas[5].stroke_style = EDITED_CELL_OUTLINE_COLOR
            for r in visible_rows:
                for c in visible_cols:
                    x = offset + (c - from_col) * cell_size
                    y = offset + (r - from_row) * cell_size
                    weights_canvas[5].stroke_rect(x, y, cell_size, cell_size)

    def _on_matrix_quadrant_changed(self, change):
        if self._last_edited_rows and self._last_edited_cols:
            self._highlight_edited_cells(self._last_edited_rows, self._last_edited_cols)

    def _build_select_nodes_popup(self):
        conn_label = getattr(self.connectivity, "title", None) or self.connectivity.gid.hex[:8]
        title = widgets.HTML(
            "<div class=\"lsc-select-nodes-title\">Connectivity - {}</div>".format(conn_label)
        )

        close_button = widgets.Button(description="\u2715", layout=widgets.Layout(width="32px"))
        close_button.add_class("lsc-select-nodes-close")
        close_button.on_click(lambda _: self._set_popup_visible(False))

        title_row = widgets.HBox(
            [title, close_button],
            layout=widgets.Layout(justify_content="space-between", align_items="center", width="100%"),
        )

        select_all_button = widgets.Button(description="Select all", layout=widgets.Layout(width="100px"))
        select_none_button = widgets.Button(description="Clear all", layout=widgets.Layout(width="100px"))
        select_all_button.on_click(lambda _: self._set_all_checkboxes(True))
        select_none_button.on_click(lambda _: self._set_all_checkboxes(False))

        self.selection_dropdown = widgets.Dropdown(
            options=[NEW_SELECTION_OPTION],
            value=NEW_SELECTION_OPTION,
            layout=widgets.Layout(width="180px"),
        )
        self.selection_dropdown.observe(self._on_selection_dropdown_change, names="value")

        self.selection_name_input = widgets.Text(
            placeholder="Selection name",
            layout=widgets.Layout(width="220px"),
        )

        save_button = widgets.Button(description="Save", layout=widgets.Layout(width="90px"))
        save_button.add_class("lsc-btn")
        save_button.on_click(self._on_save_selection)

        controls_row = widgets.HBox(
            [select_all_button, select_none_button, self.selection_dropdown,
             self.selection_name_input, save_button],
            layout=widgets.Layout(align_items="center", gap="8px", justify_content="center",
                                  margin="10px 0 14px 0"),
        )

        left_indices, right_indices = self._split_hemispheres()

        left_checkboxes = self._build_checkbox_column(left_indices)
        right_checkboxes = self._build_checkbox_column(right_indices)

        left_section = widgets.VBox(
            [widgets.HTML('<div class="lsc-select-nodes-column-title">left</div>'),
             self._grid_box(left_checkboxes)],
            layout=widgets.Layout(width="48%"),
        )
        right_section = widgets.VBox(
            [widgets.HTML('<div class="lsc-select-nodes-column-title">right</div>'),
             self._grid_box(right_checkboxes)],
            layout=widgets.Layout(width="48%"),
        )

        columns_row = widgets.HBox(
            [left_section, right_section],
            layout=widgets.Layout(justify_content="space-between", width="100%"),
        )

        scrollable = widgets.Box(
            [columns_row],
            layout=widgets.Layout(max_height="420px", overflow="auto", width="100%", padding="4px 0 0 0"),
        )

        popup = widgets.VBox(
            [title_row, controls_row, scrollable],
            layout=widgets.Layout(
                position="absolute",
                top="50px",
                left="10px",
                right="10px",
                width="auto",
                z_index="9999",
                visibility="hidden",
            ),
        )
        popup.add_class("lsc-select-nodes-popup")
        return popup

    def _build_checkbox_column(self, indices):
        checkboxes = []
        for idx in indices:
            label = str(self.connectivity.region_labels[idx])
            checkbox = widgets.Checkbox(value=True, description=label, indent=False,
                                        layout=widgets.Layout(width="150px"))
            self._node_checkboxes[idx] = checkbox
            checkboxes.append(checkbox)
        return checkboxes

    def _grid_box(self, checkboxes):
        return widgets.GridBox(
            children=checkboxes,
            layout=widgets.Layout(
                grid_template_columns="repeat({}, 150px)".format(NODE_CHECKBOX_COLUMNS),
                grid_gap="2px 10px",
            ),
        )

    def _split_hemispheres(self):
        n = len(self.connectivity.region_labels)
        hemispheres = getattr(self.connectivity, "hemispheres", None)

        if hemispheres is not None and len(hemispheres) == n:
            left_indices = [i for i in range(n) if not hemispheres[i]]
            right_indices = [i for i in range(n) if hemispheres[i]]
            return left_indices, right_indices

        half = n // 2
        return list(range(half)), list(range(half, n))

    def _set_popup_visible(self, visible):
        self.select_nodes_popup.layout.visibility = "visible" if visible else "hidden"

    def _hide_all_popups(self):
        self.select_nodes_popup.layout.visibility = "hidden"
        self.edge_operations_popup.layout.visibility = "hidden"

    def _toggle_popup(self, popup):
        currently_visible = popup.layout.visibility == "visible"
        self._hide_all_popups()
        if not currently_visible:
            popup.layout.visibility = "visible"

    def _set_all_checkboxes(self, value):
        for checkbox in self._node_checkboxes.values():
            checkbox.value = value

    def _current_mask(self):
        n = len(self.connectivity.region_labels)
        return [self._node_checkboxes[i].value for i in range(n)]

    def _on_selection_dropdown_change(self, change):
        name = change["new"]
        if name == NEW_SELECTION_OPTION:
            self.selection_name_input.value = ""
            self._set_all_checkboxes(True)
            return

        mask = self._node_selections.get(name)
        if mask is None:
            return
        self.selection_name_input.value = name
        for idx, checkbox in self._node_checkboxes.items():
            checkbox.value = bool(mask[idx])

    def _on_save_selection(self, change):
        name = self.selection_name_input.value.strip()
        if not name:
            name = "Selection {}".format(len(self._node_selections) + 1)

        mask = self._current_mask()
        self._node_selections[name] = mask
        self._active_node_mask = mask

        options = [NEW_SELECTION_OPTION] + list(self._node_selections.keys())
        self.selection_dropdown.unobserve(self._on_selection_dropdown_change, names="value")
        self.selection_dropdown.options = options
        self.selection_dropdown.value = name
        self.selection_dropdown.observe(self._on_selection_dropdown_change, names="value")

        self.head_widget.set_node_selection(self.connectivity, mask)

    def _on_edge_operations_click(self, change):
        self._set_edge_operation_error("")
        self._toggle_popup(self.edge_operations_popup)

    def _on_select_nodes_click(self, change):
        self._toggle_popup(self.select_nodes_popup)

    def _on_reset_edits_click(self, change):
        editor = self.matrix_editor
        editor.new_connectivity = editor._prepare_new_connectivity()
        editor.is_connectivity_being_edited = False

        editor._update_matrices_view(editor.new_connectivity)
        editor.weights_matrix[5].clear()
        editor.tract_lengths_matrix[5].clear()

        self._last_edited_rows, self._last_edited_cols = [], []
        self.head_widget.refresh_edges(editor.new_connectivity, editor.new_connectivity.weights)
        self.head_widget.highlight_node_edges(editor.new_connectivity, self.node_dropdown.value, None)

        self._active_node_mask = [True] * len(self.connectivity.region_labels)
        self._set_all_checkboxes(True)
        self.selection_name_input.value = ""

        self.selection_dropdown.unobserve(self._on_selection_dropdown_change, names="value")
        self.selection_dropdown.value = NEW_SELECTION_OPTION
        self.selection_dropdown.observe(self._on_selection_dropdown_change, names="value")

        self.head_widget.set_node_selection(self.connectivity, self._active_node_mask)

    def display(self):
        from IPython.display import display

        display(self)
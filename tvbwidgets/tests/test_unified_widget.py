# -*- coding: utf-8 -*-
#
# "TheVirtualBrain - Widgets" package
#
# (c) 2022-2025, TVB Widgets Team
#

import matplotlib
import numpy as np
import pytest
from tvb.datatypes.connectivity import Connectivity
from tvbwidgets.ui.connectivity_matrix_editor_widget import load_connectivity_h5
from tvbwidgets.ui.Unified_widget.Unified_widget import (
    LargeScaleConnectivityWidget,
    EXPORT_TOOLTIP,
    NEW_SELECTION_OPTION,
)
from tvbwidgets.ui.Unified_widget.helper_widget import NODE_EDGE_COLORS, UNSELECTED_NODE_COLOR

matplotlib.use('Agg')

@pytest.fixture
def connectivity():
    conn = Connectivity.from_file()
    conn.configure()
    return conn

@pytest.fixture
def wid(connectivity):
    return LargeScaleConnectivityWidget(connectivity)

def unselect(wid, node):
    mask = [True] * len(wid.connectivity.region_labels)
    mask[node] = False
    wid._active_node_mask = mask

def edge_operation(wid, operation, edge_type, value):
    wid.operation_dropdown.value = operation
    wid.edge_type_dropdown.value = edge_type
    wid.weight_change_input.value = value
    wid._on_apply_edge_operation(None)

def edit_cell(wid, row, col, value):
    editor = wid.matrix_editor
    editor.clicked_matrix = "weights"
    editor.row, editor.col = row, col
    editor.popup.layout.visibility = "visible"
    editor.popup_value.value = value
    editor.popup_change.click()

def click(wid, node, direction):
    wid.node_dropdown.value = node
    wid._on_node_direction_click(direction)

def node_edges(wid, node):
    lines = wid.head_widget._node_edge_objects.get(node)
    return None if lines is None else lines.indices.tolist()

def save_selection(wid, name, unchecked):
    wid._set_all_checkboxes(True)
    for node in unchecked:
        wid._node_checkboxes[node].value = False
    wid.selection_name_input.value = name
    wid._on_save_selection(None)

def test_layout(wid):
    view_panel, control_panel = wid.children[1].children
    assert "VIEW" in view_panel.children[0].value
    assert "CONTROL" in control_panel.children[0].value
    assert view_panel.children[1] is wid.view_subtabs
    assert [wid.view_subtabs.get_title(i) for i in range(2)] == ["Head View", "Space Time"]
    assert wid.matrix_editor.export_button.tooltip == EXPORT_TOOLTIP

def test_conn_edited(wid):
    wid.matrix_editor.new_connectivity.weights[0][2] = 5
    assert np.array_equal(wid.conn_edited.weights, wid.matrix_editor.new_connectivity.weights)
    assert len(wid.conn_edited.saved_selection) == len(wid.connectivity.region_labels)

    unselect(wid, 1)
    branch = wid.conn_edited
    assert branch.weights[0][2] == 5
    assert branch.weights[1].sum() == 0
    assert branch.weights[:, 1].sum() == 0
    assert 1 not in branch.saved_selection
    assert wid.matrix_editor.new_connectivity.weights[1].sum() > 0

def test_export_button(wid, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    wid.matrix_editor.new_connectivity.weights[0][2] = 5
    unselect(wid, 1)

    wid.matrix_editor.export_button.click()
    loaded = load_connectivity_h5(str(tmp_path / "edited_connectivity_1.h5"))
    assert loaded.weights[0][2] == 5
    assert loaded.weights[0][3] == wid.connectivity.weights[0][3]
    assert loaded.weights[1].sum() == 0
    assert loaded.weights[:, 1].sum() == 0
    assert 1 not in loaded.saved_selection
    assert sorted(p.name for p in tmp_path.iterdir()) == ["edited_connectivity_1.h5"]

def test_cell_change_updates_views(wid):
    edit_cell(wid, 0, 2, "5")
    connectivity = wid.matrix_editor.new_connectivity
    assert connectivity.weights[0][2] == 5
    edges = wid.head_widget._find_lines_object(connectivity)
    assert [0, 2] in edges.indices.tolist()
    assert wid.space_time_widget.connectivity.weights[0][2] == 5

def test_invalid_cell_value_changes_nothing(wid, monkeypatch):
    calls = []
    monkeypatch.setattr(wid, "_update_space_time", lambda: calls.append(1))
    original = wid.matrix_editor.new_connectivity.weights[0][1]
    edit_cell(wid, 0, 1, "abc")
    assert wid.matrix_editor.new_connectivity.weights[0][1] == original
    assert calls == []

@pytest.mark.parametrize("operation, value, expected", [
    ("Set", "7", 7),
    ("Add", "1", 3),
    ("Subtract", "5", 0),
    ("Multiply", "2", 4),
    ("Divide", "2", 1),
])
def test_edge_operations(wid, operation, value, expected):
    edge_operation(wid, operation, "In -> In", value)
    assert wid.matrix_editor.new_connectivity.weights[0][1] == expected
    assert wid.space_time_widget.connectivity.weights[0][1] == expected

def test_edge_types(wid):
    unselect(wid, 1)
    edge_operation(wid, "Set", "In -> Out", "7")
    weights = wid.matrix_editor.new_connectivity.weights
    assert weights[0][1] == 7
    assert weights[1][0] == 3
    assert weights[0][3] == 2

    edge_operation(wid, "Set", "Out -> In", "8")
    assert weights[1][0] == 8
    assert weights[0][1] == 7

    edge_operation(wid, "Set", "Out -> Out", "9")
    assert weights[1][1] == 9
    assert weights[0][1] == 7

@pytest.mark.parametrize("value, operation, edge_type, message", [
    ("abc", "Set", "In -> In", "must be a number"),
    ("nan", "Set", "In -> In", "must be a finite number"),
    ("0", "Divide", "In -> In", "Division by zero"),
    ("1", "Set", "Out -> Out", "No edges of this type"),
])
def test_edge_operation_errors(wid, value, operation, edge_type, message):
    original = wid.matrix_editor.new_connectivity.weights.copy()
    edge_operation(wid, operation, edge_type, value)
    assert message in wid.edge_operation_error_label.value
    assert np.array_equal(wid.matrix_editor.new_connectivity.weights, original)
    assert wid._last_edited_matrix is None

def test_edge_operation_on_tract_lengths(wid):
    weights = wid.matrix_editor.new_connectivity.weights.copy()
    wid.matrix_editor.tab.selected_index = 1
    edge_operation(wid, "Set", "In -> In", "7")
    assert wid.matrix_editor.new_connectivity.tract_lengths[0][1] == 7
    assert wid.space_time_widget.connectivity.tract_lengths[0][1] == 7
    assert np.array_equal(wid.matrix_editor.new_connectivity.weights, weights)
    assert wid._last_edited_matrix == "tract_lengths"

def test_edited_cells_outline(wid, monkeypatch):
    unselect(wid, 1)
    edge_operation(wid, "Set", "In -> Out", "7")
    assert wid._last_edited_matrix == "weights"
    assert wid._last_edited_cols == [1]
    assert 1 not in wid._last_edited_rows

    drawn = []
    monkeypatch.setattr(wid, "_highlight_edited_cells", lambda *args: drawn.append(args))
    wid.matrix_editor.quadrants.value = "Quadrant 2"
    assert drawn[-1] == ("weights", wid._last_edited_rows, [1])

def test_base_edges_hidden(wid):
    assert not wid.head_widget._find_lines_object(wid.connectivity).visible

def test_node_edges_toggle(wid):
    targets = np.nonzero(wid.connectivity.weights[0])[0]
    click(wid, 0, "outgoing")
    assert node_edges(wid, 0) == [[0, j] for j in targets if j != 0]
    assert wid.outgoing_button.description == "Hide outgoing"

    click(wid, 2, "incoming")
    assert wid.head_widget._node_edge_objects[0].color == NODE_EDGE_COLORS[0]
    assert wid.head_widget._node_edge_objects[2].color == NODE_EDGE_COLORS[1]

    click(wid, 0, "outgoing")
    assert node_edges(wid, 0) is None
    assert wid.outgoing_button.description == "Show outgoing"

    wid._clear_node_edges()
    assert wid.head_widget._node_edge_objects == {}

def test_hide_incoming_hides_shared_edge(wid):
    target = [j for j in np.nonzero(wid.connectivity.weights[0])[0] if j != 0][0]
    click(wid, 0, "outgoing")
    wid.node_dropdown.value = target
    assert wid.incoming_button.description == "Hide incoming"

    wid._on_node_direction_click("incoming")
    assert [0, target] not in node_edges(wid, 0)

def test_node_edges_follow_edits(wid):
    new_target = [j for j in range(1, 38) if wid.connectivity.weights[0][j] == 0][0]
    click(wid, 0, "outgoing")
    edit_cell(wid, 0, new_target, "5")
    assert [0, new_target] in node_edges(wid, 0)

    edge_operation(wid, "Set", "In -> In", "0")
    assert node_edges(wid, 0) is None

def test_save_selection(wid):
    save_selection(wid, "sel", unchecked=[1])
    assert wid._node_selections["sel"][1] is False
    assert wid._active_node_mask[1] is False
    assert wid.selection_dropdown.value == "sel"

    points = wid.head_widget._find_points_object(wid.connectivity)
    assert points.colors[1] == UNSELECTED_NODE_COLOR
    assert points.colors[0] != UNSELECTED_NODE_COLOR

@pytest.mark.parametrize("name", ["", "   ", NEW_SELECTION_OPTION])
def test_invalid_selection_name(wid, name):
    save_selection(wid, name, unchecked=[1])
    assert wid.selection_error_label.value != ""
    assert wid._node_selections == {}
    assert all(wid._active_node_mask)

def test_choose_selection_from_dropdown(wid):
    save_selection(wid, "sel", unchecked=[1])
    wid.selection_dropdown.value = NEW_SELECTION_OPTION
    assert not any(checkbox.value for checkbox in wid._node_checkboxes.values())
    assert wid.selection_name_input.value == ""

    wid.selection_dropdown.value = "sel"
    assert wid._node_checkboxes[1].value is False
    assert wid._node_checkboxes[0].value is True
    assert wid.selection_name_input.value == "sel"

def test_selection_counter(wid):
    assert wid.selection_counter.value == "Selected 76 of 76 nodes"
    save_selection(wid, "sel", unchecked=[1, 2])
    assert wid.selection_counter.value == "Selected 74 of 76 nodes"

    wid.selection_dropdown.value = NEW_SELECTION_OPTION
    assert wid.selection_counter.value == "Selected 74 of 76 nodes"

    wid._on_reset_edits_click(None)
    assert wid.selection_counter.value == "Selected 76 of 76 nodes"

def test_select_and_clear_all(wid):
    wid._set_all_checkboxes(False)
    assert not any(wid._current_mask())
    wid._set_all_checkboxes(True)
    assert all(wid._current_mask())

def test_hemisphere_toggle(wid):
    left, right = wid._split_hemispheres()
    wid._node_checkboxes[left[0]].value = False

    wid._toggle_checkboxes(left)
    assert all(wid._node_checkboxes[idx].value for idx in left)

    wid._toggle_checkboxes(left)
    assert not any(wid._node_checkboxes[idx].value for idx in left)
    assert all(wid._node_checkboxes[idx].value for idx in right)

def test_popups_toggle(wid):
    wid._on_edge_operations_click(None)
    assert wid.edge_operations_popup.layout.visibility == "visible"

    wid._on_select_nodes_click(None)
    assert wid.select_nodes_popup.layout.visibility == "visible"
    assert wid.edge_operations_popup.layout.visibility == "hidden"

    wid._on_select_nodes_click(None)
    assert wid.select_nodes_popup.layout.visibility == "hidden"

def test_reset(wid):
    original = wid.connectivity.weights[0][1]
    wid.node_dropdown.value = 0
    wid._on_node_direction_click("outgoing")
    save_selection(wid, "sel", unchecked=[5])
    edge_operation(wid, "Set", "In -> In", "7")
    assert wid.matrix_editor.new_connectivity.weights[0][1] == 7

    wid._on_reset_edits_click(None)
    assert wid.matrix_editor.new_connectivity.weights[0][1] == original
    assert wid.space_time_widget.connectivity.weights[0][1] == original
    assert wid._last_edited_matrix is None
    assert all(wid._active_node_mask)
    assert wid.selection_dropdown.value == NEW_SELECTION_OPTION
    assert wid.head_widget._node_edge_objects == {}

def test_same_colors_in_matrix_and_space_time(connectivity):
    widget = LargeScaleConnectivityWidget(connectivity, color_scheme="viridis")
    editor, space_time = widget.matrix_editor, widget.space_time_widget
    assert editor.color_scheme.name == space_time.color_scheme.name == "viridis"

    values = np.array([[0.0, 1.0, 3.0]])
    editor_colors = editor._generate_color(connectivity, value=values, matrix_name="weights") / 255
    assert np.allclose(editor_colors, space_time._custom_colormap(values))
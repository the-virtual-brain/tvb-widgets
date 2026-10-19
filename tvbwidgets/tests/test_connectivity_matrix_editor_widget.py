# -*- coding: utf-8 -*-
#
# "TheVirtualBrain - Widgets" package
#
# (c) 2022-2025, TVB Widgets Team
#

import math
import pytest
import numpy as np
import ipycanvas as canvas
import ipywidgets as widgets
import matplotlib.colors as mcolors
from tvb.datatypes.connectivity import Connectivity
from tvbwidgets.ui.connectivity_matrix_editor_widget import ConnectivityMatrixEditor, load_connectivity_h5

@pytest.fixture
def connectivity():
    conn = Connectivity.from_file()
    conn.configure()
    return conn

@pytest.fixture
def wid(connectivity):
    widget = ConnectivityMatrixEditor(connectivity)
    return widget

def test_display(wid):
    wid.display()
    assert isinstance(wid, ConnectivityMatrixEditor)

def test_make_header(wid):
    assert len(wid.header.children) == 5
    assert isinstance(wid.header.children[0], widgets.Dropdown)
    assert isinstance(wid.header.children[2], widgets.Text)
    assert isinstance(wid.header.children[4], widgets.Button)

def test_get_quadrant_range(wid):
    wid._get_quadrant_range(selection = 1)
    assert wid.from_row == 0
    assert wid.from_col == 0
    wid._get_quadrant_range(selection = 2)
    assert wid.from_row == 38
    assert wid.from_col == 0
    wid._get_quadrant_range(selection = 3)
    assert wid.from_row == 0
    assert wid.from_col == 38
    wid._get_quadrant_range(selection = 4)
    assert wid.from_col == 38
    assert wid.from_row == 38

def test_prepare_matrices_tab(wid):
    assert isinstance(wid.weights_matrix, canvas.canvas.MultiCanvas)
    assert isinstance(wid.tract_lengths_matrix, canvas.canvas.MultiCanvas)
    assert len(wid.tab.children) == 2
    assert wid.tab.get_title(0) == "weights"
    assert wid.tab.get_title(1) == "tract_lengths"

def test_prepare_matrix(wid):
    assert math.isclose(wid.cell_size, 16.43, abs_tol=0.1)
    assert math.isclose(wid.weights_matrix.width, 926, abs_tol=1)
    assert math.isclose(wid.weights_matrix.height, 912, abs_tol=1)
    assert math.isclose(wid.tract_lengths_matrix.width, 926, abs_tol=1)
    assert math.isclose(wid.tract_lengths_matrix.height, 912, abs_tol=1)
    assert isinstance(wid.weights_matrix[0], canvas.canvas.Canvas)
    assert isinstance(wid.weights_matrix[1], canvas.canvas.Canvas)
    assert isinstance(wid.weights_matrix[2], canvas.canvas.Canvas)
    assert isinstance(wid.weights_matrix[3], canvas.canvas.Canvas)
    assert isinstance(wid.weights_matrix[4], canvas.canvas.Canvas)
    assert isinstance(wid.weights_matrix[5], canvas.canvas.Canvas)
    assert isinstance(wid.tract_lengths_matrix[0], canvas.canvas.Canvas)
    assert isinstance(wid.tract_lengths_matrix[1], canvas.canvas.Canvas)
    assert isinstance(wid.tract_lengths_matrix[2], canvas.canvas.Canvas)
    assert isinstance(wid.tract_lengths_matrix[3], canvas.canvas.Canvas)
    assert isinstance(wid.tract_lengths_matrix[4], canvas.canvas.Canvas)
    assert isinstance(wid.tract_lengths_matrix[5], canvas.canvas.Canvas)

def rgba_text(color):
    return f"rgba({color[0] * 255:.0f}, {color[1] * 255:.0f}, {color[2] * 255:.0f}, {color[3]:.2f})"

def test_generate_color_with_indices(wid, connectivity):
    empty_color = rgba_text(mcolors.to_rgba(wid.empty_cell_color))
    assert wid._generate_color(connectivity, i=20, j=38, matrix_name="weights") == empty_color

    tract_lengths = connectivity.tract_lengths
    expected = rgba_text(wid.color_scheme(tract_lengths[5][70] / tract_lengths.max()))
    assert wid._generate_color(connectivity, i=5, j=70, matrix_name="tract_lengths") == expected

def test_generate_color_with_single_value(wid, connectivity):
    expected = rgba_text(wid.color_scheme(2 / connectivity.weights.max()))
    assert wid._generate_color(connectivity, value=2, matrix_name="weights") == expected

def test_generate_color_with_array_value(wid, connectivity):
    value = np.array([[0, 2], [2, 3]])
    colors = wid._generate_color(connectivity, value=value, matrix_name="weights")
    expected = wid.color_scheme(value / connectivity.weights.max())[:, :, :3] * 255
    expected[0][0] = np.array(mcolors.to_rgb(wid.empty_cell_color)) * 255
    assert np.allclose(colors, expected)

def test_color_scheme(connectivity):
    widget = ConnectivityMatrixEditor(connectivity, color_scheme="viridis")
    assert widget.color_scheme.name == "viridis"
    assert widget._colorbar_stops()[0][1] == mcolors.to_hex(widget.color_scheme(1.0))
    assert widget._colorbar_stops()[-1][1] == mcolors.to_hex(widget.color_scheme(0.0))

    with pytest.raises(ValueError):
        ConnectivityMatrixEditor(connectivity, color_scheme="not a colormap")

def test_prepare_new_connectivity(wid):
    conn = wid._prepare_new_connectivity()
    assert isinstance(conn, Connectivity)
    assert wid.new_connectivity.parent_connectivity == wid.connectivity.gid.hex
    assert wid.new_connectivity.centres.all() == wid.connectivity.centres.all()
    assert wid.new_connectivity.orientations.all() == wid.connectivity.orientations.all()
    assert wid.new_connectivity.cortical.all() == wid.connectivity.cortical.all()
    assert wid.new_connectivity.hemispheres.all() == wid.connectivity.hemispheres.all()
    assert wid.new_connectivity.areas.all() == wid.connectivity.areas.all()
    assert wid.new_connectivity.weights.all() == wid.connectivity.weights.all()
    assert wid.new_connectivity.tract_lengths.all() == wid.connectivity.tract_lengths.all()

def test_edit_cell_value(wid):
    wid.clicked_matrix = "weights"
    wid.row, wid.col = 0, 1
    original = wid.new_connectivity.weights[0][1]

    for text in ("abc", "nan", "inf"):
        wid.popup_value.value = text
        wid.on_apply_change(None)
        assert wid.new_connectivity.weights[0][1] == original
        assert wid.popup_error.value != ""

    wid.on_click_cancel()
    assert wid.popup_error.value == ""

    wid.popup_value.value = "-2"
    wid.on_apply_change(None)
    assert wid.new_connectivity.weights[0][1] == 0

def test_conn_edited(wid):
    conn = wid.conn_edited
    conn.weights[0][1] = 100
    assert wid.new_connectivity.weights[0][1] != 100
    assert conn.parent_connectivity == wid.connectivity.gid.hex

def test_export_h5(wid, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    wid.new_connectivity.weights[0][1] = 5
    wid.export_name.value = "my_conn"

    path = wid.export_h5(wid.conn_edited)
    assert load_connectivity_h5(path).weights[0][1] == 5
    assert wid.export_name.value == "edited_connectivity_1"

    wid.new_connectivity.weights[0][1] = 9
    wid.export_name.value = "my_conn"
    assert wid.export_h5(wid.conn_edited) is None
    assert load_connectivity_h5(path).weights[0][1] == 5

    wid.export_name.value = "my-conn"
    assert wid.export_h5(wid.conn_edited) is None
    assert sorted(p.name for p in tmp_path.iterdir()) == ["my_conn.h5"]

def test_load_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_connectivity_h5(str(tmp_path / "missing.h5"))
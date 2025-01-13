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
from tvb.datatypes.connectivity import Connectivity
from tvbwidgets.ui.connectivity_matrix_editor_widget import ConnectivityMatrixEditor

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
    assert isinstance(wid.header.children[1], widgets.Text)
    assert isinstance(wid.header.children[2], widgets.Button)
    assert isinstance(wid.header.children[3], widgets.Button)
    assert isinstance(wid.header.children[4], widgets.Dropdown)

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
    assert math.isclose(wid.weights_matrix.width, 1140, abs_tol=1)
    assert math.isclose(wid.weights_matrix.height, 912, abs_tol=1)
    assert math.isclose(wid.tract_lengths_matrix.width, 1140, abs_tol=1)
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

def test_generate_color_with_indices(wid, connectivity):
    color = wid._generate_color(connectivity, i=20, j=38, matrix_name="weights")
    assert color == 'rgba(102, 121, 123, 1.00)'    
    color = wid._generate_color(connectivity, i=5, j=70, matrix_name="tract_lengths")
    assert color == 'rgba(38, 124, 105, 1.00)'
    
def test_generate_color_with_single_value(wid, connectivity):
    color = wid._generate_color(connectivity, value = 2, matrix_name="weights")
    assert color == 'rgba(145, 224, 255, 1.00)' 
    color = wid._generate_color(connectivity, value = 3, matrix_name = "tract_lengths")
    assert color == 'rgba(97, 101, 108, 1.00)'

def test_generate_color_with_array_value(wid, connectivity):
    value = np.array([[1, 2], [2, 3]])
    colors = wid._generate_color(connectivity, value = value, matrix_name="weights")
    assert np.allclose(colors, [[[ 61.33333333, 170.66666667,  62.        ],
                                        [145.        , 224.33333333, 255.        ]],
                                        [[145.        , 224.33333333, 255.        ],
                                        [251.        ,  82.        ,  38.        ]]])
    
    colors = wid._generate_color(connectivity, value = value, matrix_name="tract_lengths")
    assert np.allclose(colors, [[[101.01176471, 117.04705882, 120.09019608],
                                  [ 99.03529412, 109.14117647, 114.27058824]],
                                  [[ 99.03529412, 109.14117647, 114.27058824],
                                  [ 97.05882353, 101.23529412, 108.45098039]]])

def test_saved_connectivities(wid):
    conn_list = wid.saved_connectivities()
    assert conn_list is not None
    assert isinstance(conn_list, list)
    assert isinstance(conn_list[0], str)

def test_get_connectivity(wid):
    conn = wid.get_connectivity()
    assert isinstance(conn, Connectivity)
    assert conn == wid.connectivity

def test_on_click_save(wid):
    wid.save_button.click()
    assert len(wid.connectivity_history_list) == 2

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
import pytest
import numpy as np
import pythreejs as p3
import matplotlib
from ipywidgets import Tab, Output, BoundedFloatText, FloatText
from tvbwidgets.ui.spacetime_widget import SpaceTimeVisualizerWidget
from tvb.datatypes.connectivity import Connectivity

matplotlib.use('Agg')

@pytest.fixture
def connectivity():
    conn = Connectivity.from_file()
    conn.configure()
    return conn

@pytest.fixture
def wid(connectivity):
    widget = SpaceTimeVisualizerWidget(connectivity)
    return widget

def test_display(wid):
    wid.display()
    assert isinstance(wid, SpaceTimeVisualizerWidget)

def test_prepare_tabs(wid):
    assert isinstance(wid.tab, Tab)
    assert len(wid.tab.children) == 2
    assert isinstance(wid.tab.children[0], Output)
    assert isinstance(wid.tab.children[1], Output)
    assert isinstance(wid.renderer, p3.Renderer)
    assert isinstance(wid.fig, matplotlib.figure.Figure)

def test_prepare_scene(wid):
    assert isinstance(wid.scene, p3.Scene)
    assert isinstance(wid.camera, p3.PerspectiveCamera)
    assert isinstance(wid.light, p3.AmbientLight)
    assert isinstance(wid.key_light, p3.DirectionalLight)
    assert isinstance(wid.picker, p3.Picker)
    assert isinstance(wid.renderer, p3.Renderer)

def test_prepare_slices(wid):
    assert len(wid.graph_slices) == 7
    assert wid.graph_slices[0].material.map is not None
    for i in range(7):
        assert wid.graph_slices[i] in wid.scene.children

def tests_create_graph_slice(wid):
    assert wid.graph_slices[0].geometry.height == 7.0
    assert wid.graph_slices[0].geometry.width == 7.0
    assert wid.graph_slices[0].geometry.depth == 0.1
    for i in range(len(wid.graph_slices)):
        z = -i*3.0 + 10.0
        assert wid.graph_slices[i].position == (15.0, 0.0, z)

def test_generate_texture(wid):
    for i in range(7):
        texture = wid._generate_texture(i)
        assert texture.format == "RGBFormat"
        assert texture.data.shape == (76, 76, 3)


def test_generate_colors(wid):
    colors = wid._generate_colors(wid.connectivity.weights)
    assert colors is not None
    assert colors.shape == (76, 76, 3)

def test_prepare_grid(wid):
    wid._prepare_grid()
    assert isinstance(wid.grid, p3.Mesh)
    assert wid.grid.material.map is not None
    assert wid.grid.material.transparent == True
    assert wid.grid.position == (0, 0, 0)
    assert wid.grid.name == "grid"
    assert wid.grid.scale == (4, 3, 1)

def test_generate_gridlines(wid):
    grid = wid._generate_gridlines()
    expected_grid = np.zeros((76, 76, 4))
    repetition_pattern = np.ones((5, 5, 1))
    expected_grid = np.kron(expected_grid, repetition_pattern)
    size = expected_grid.shape[0]
    mask = (np.arange(size) % 5 == 0)[:, None] | (np.arange(size) % 5 == 0)[None, :]
    expected_grid[mask] = [0, 0, 0, 1]
    assert grid.format == "RGBAFormat"
    assert grid.data.shape == (76*5, 76*5, 4)
    assert (grid.data == expected_grid).all

def test_prepare_connectivity(wid):
    i = 2
    slice_range = (( wid.to_time- wid.from_time) * i) /  wid.num_slices
    prev_slice_range =  (( wid.to_time- wid.from_time) * (i - 1)) /  wid.num_slices
    time_delay =  wid.connectivity.tract_lengths *  wid.conduction_speed
    mask = (time_delay < slice_range) & (time_delay > prev_slice_range) 
    expected_connectivity = np.where(mask,  wid.connectivity.weights, 0)
    connectivity = wid._prepare_connectivity(2)
    assert (connectivity == expected_connectivity).all

def test_create_matplotlib_graphs(wid):
    assert len(wid.ims) == 7
    assert len(wid.fig.axes) == 7
    assert wid.fig.get_figheight() == 10.0
    assert wid.fig.get_figwidth() == 14.0

def test_add_options(wid):
    assert len(wid.options.children) == 3
    assert isinstance(wid.options.children[0], FloatText)
    assert isinstance(wid.options.children[1], BoundedFloatText)
    assert isinstance(wid.options.children[2], BoundedFloatText)

    assert wid.options.children[1].description == "from[ms]:"
    assert wid.options.children[2].description == "to[ms]:"
    assert wid.options.children[0].value == 1.0
    assert wid.options.children[0].description == "Conduction Speed:"
    assert wid.options.children[1].value == 0.0
    assert wid.options.children[1].min == 0.0
    assert wid.options.children[1].max == 153.49
    assert wid.options.children[2].value == 153.49
    assert wid.options.children[2].min == 0.0
    assert wid.options.children[2].max == 153.49




    



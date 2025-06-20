import k3d
import math
import pytest
import matplotlib
from ipywidgets import Tab, Output, BoundedFloatText, Text, HBox, HTML
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

def test_prepare_widget(wid):
    assert isinstance(wid.hbox, HBox)
    assert len(wid.hbox.children) == 2
    assert isinstance(wid.hbox.children[0], Tab)
    assert isinstance(wid.hbox.children[1], HTML)
    assert isinstance(wid.tab, Tab)
    assert len(wid.tab.children) == 2
    assert isinstance(wid.tab.children[0], Output)
    assert isinstance(wid.tab.children[1], Output)
    assert isinstance(wid.plot, k3d.Plot)
    assert isinstance(wid.fig, matplotlib.figure.Figure)

def test_prepare_scene(wid):
    assert len(wid.plot.objects) == wid.num_slices + 1
    for texture in wid.plot.objects:
        assert isinstance(texture, k3d.objects.Texture)

def test_custom_colormap(wid):
    colors = wid._custom_colormap(wid.connectivity.weights)
    assert colors is not None
    assert colors.shape == (76, 76, 3)

def test_prepare_connectivity(wid):
    connectivity = wid._prepare_connectivity(2)
    assert connectivity.shape == (76, 76)

def test_create_plots_overview(wid):
    assert len(wid.ims) == 7
    assert len(wid.fig.axes) == 7
    assert math.isclose(wid.fig.get_figheight(), 600/75.65)
    assert math.isclose(wid.fig.get_figwidth(), 900/75.65)

def test_add_options(wid):
    assert len(wid.options.children) == 4
    assert isinstance(wid.options.children[0], BoundedFloatText)
    assert isinstance(wid.options.children[1], BoundedFloatText)
    assert isinstance(wid.options.children[2], BoundedFloatText)
    assert isinstance(wid.options.children[3], Text)

    assert wid.options.children[1].description == "From[ms]:"
    assert wid.options.children[2].description == "To[ms]:"
    assert wid.options.children[3].description == "Selection[ms]:"
    assert math.isclose(wid.options.children[0].value, 1.0)
    assert wid.options.children[0].description == "Conduction Speed:"
    assert math.isclose(wid.options.children[1].value, 0.0)
    assert math.isclose(wid.options.children[1].min, 0.0)
    assert math.isclose(wid.options.children[1].max, 153.48574)
    assert math.isclose(wid.options.children[2].value, 153.48574)
    assert math.isclose(wid.options.children[2].min, 0.0)
    assert math.isclose(wid.options.children[2].max, 153.48574)
    assert wid.options.children[3].value == "None"




    



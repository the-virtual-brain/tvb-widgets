import k3d
import math
import numpy
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


def test_default_border_not_mutated(wid):
    from tvbwidgets.ui.base_widget import TVBWidget
    assert 'min_width' not in TVBWidget.DEFAULT_BORDER, (
        "SpaceTimeVisualizerWidget mutated the shared TVBWidget.DEFAULT_BORDER. "
        "Use layout = {**self.DEFAULT_BORDER} instead of layout = self.DEFAULT_BORDER."
    )

def test_all_weights_zero(connectivity):
    connectivity.weights = numpy.zeros_like(connectivity.weights)
    widget = SpaceTimeVisualizerWidget(connectivity)
    assert isinstance(widget.plot_details, HTML)


def test_all_tract_lengths_zero(connectivity):
    connectivity.tract_lengths = numpy.zeros_like(connectivity.tract_lengths)
    widget = SpaceTimeVisualizerWidget(connectivity)
    speed = widget.option_conduction_speed
    assert speed.min <= speed.value <= speed.max

def test_same_color_range_for_all_slices(connectivity):
    connectivity.weights = numpy.where(connectivity.tract_lengths > 80, 1.0, 3.0)
    widget = SpaceTimeVisualizerWidget(connectivity)
    ranges = {tuple(texture.color_range) for texture in widget.plot.objects}
    assert len(ranges) == 1

def test_color_range_not_empty(connectivity):
    for value in (0.0, 5.0):
        connectivity.weights = numpy.full_like(connectivity.weights, value)
        widget = SpaceTimeVisualizerWidget(connectivity)
        for texture in widget.plot.objects:
            assert texture.color_range[0] < texture.color_range[1]

def test_plots_overview_uses_max_weight(connectivity):
    connectivity.weights = numpy.where(connectivity.tract_lengths > 80, 3.0, 10.0)
    widget = SpaceTimeVisualizerWidget(connectivity)
    colors = widget._custom_colormap(numpy.array([[3.0, 10.0]]))
    assert not numpy.allclose(colors[0][0], colors[0][1])

def test_update_connectivity(connectivity):
    widget = SpaceTimeVisualizerWidget(connectivity)
    plot = widget.plot
    new_connectivity = Connectivity.from_file()
    new_connectivity.weights = new_connectivity.weights * 2
    new_connectivity.configure()
    widget.update_connectivity(new_connectivity)
    assert widget.plot is plot
    assert numpy.allclose(widget.plot.objects[0].attribute, new_connectivity.weights)

def test_update_connectivity_keeps_time_interval(connectivity):
    widget = SpaceTimeVisualizerWidget(connectivity)
    widget.option_from_time.value = 20.0
    widget.option_to_time.value = 60.0
    widget.update_connectivity(connectivity)
    assert math.isclose(widget.option_from_time.value, 20.0)
    assert math.isclose(widget.option_to_time.value, 60.0)

def test_update_connectivity_changes_time_limits(connectivity):
    widget = SpaceTimeVisualizerWidget(connectivity)
    longer = Connectivity.from_file()
    longer.tract_lengths = numpy.full_like(longer.tract_lengths, 200.0)
    longer.configure()
    widget.update_connectivity(longer)
    assert math.isclose(widget.option_from_time.min, 200.0)
    assert math.isclose(widget.option_to_time.max, 200.0)
    widget.update_connectivity(connectivity)
    assert math.isclose(widget.option_from_time.min, connectivity.tract_lengths.min())
    assert math.isclose(widget.option_to_time.max, connectivity.tract_lengths.max())
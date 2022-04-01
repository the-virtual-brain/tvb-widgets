import logging
import numpy
import tvbwidgets.api as api

from tvb.datatypes.connectivity import Connectivity
from tvb.datatypes.region_mapping import RegionMapping
from tvb.datatypes.sensors import SensorsInternal
from tvb.datatypes.surfaces import FaceSurface, CorticalSurface


def test_add_datatype(caplog, mocker):
    def mock_update_plot(self):
        """Mock plot drawing"""
        pass

    mocker.patch('tvbwidgets.ui.threed_widget.CustomOutput.update_plot', mock_update_plot)

    connectivity = Connectivity(centres=numpy.zeros((10, 3)))
    widget = api.ThreeDWidget([connectivity])
    assert widget.output_plot.total_actors == 1
    assert len(widget.plot_controls.children) == 1

    caplog.clear()
    with caplog.at_level(logging.DEBUG):
        api.ThreeDWidget(None)
        assert caplog.records[0].levelname == 'WARNING'
        assert 'not supported' in caplog.text

    widget = api.ThreeDWidget()

    caplog.clear()
    with caplog.at_level(logging.DEBUG):
        widget.add_datatype(None)
        assert caplog.records[0].levelname == 'INFO'
        assert 'None' in caplog.text

    caplog.clear()
    widget.add_datatype(RegionMapping())
    assert caplog.records[0].levelname == 'INFO'
    assert 'cmap' in caplog.text

    caplog.clear()
    widget.add_datatype(10)
    assert caplog.records[0].levelname == 'WARNING'
    assert 'not supported' in caplog.text

    widget.add_datatype(connectivity)
    assert widget.output_plot.total_actors == 1
    assert len(widget.plot_controls.children) == 1

    face = FaceSurface(vertices=numpy.zeros((10, 3)), triangles=numpy.zeros((10, 3), dtype=int))
    widget.add_datatype(face)
    assert widget.output_plot.total_actors == 2
    assert len(widget.plot_controls.children) == 2
    assert len(widget.surface_display_controls.children) == 1

    seeg = SensorsInternal(locations=numpy.zeros((10, 3)))
    widget.add_datatype(seeg)
    assert widget.output_plot.total_actors == 3
    assert len(widget.plot_controls.children) == 3

    cortex = CorticalSurface(vertices=numpy.zeros((10, 3)), triangles=numpy.zeros((10, 3), dtype=int))
    reg_map = RegionMapping(array_data=numpy.zeros(10, dtype=int))
    config = api.Config(name='Cortex')
    config.add_region_mapping_as_cmap(reg_map)
    widget.add_datatype(cortex)
    assert widget.output_plot.total_actors == 4
    assert len(widget.plot_controls.children) == 4
    assert len(widget.surface_display_controls.children) == 2

    left_spots = widget.output_plot.MAX_ACTORS - widget.output_plot.total_actors

    caplog.clear()
    for _ in range(left_spots + 1):
        widget.add_datatype(connectivity)
    assert caplog.records[0].levelname == 'INFO'
    assert 'reached the maximum' in caplog.text

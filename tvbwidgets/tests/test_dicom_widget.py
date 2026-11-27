# -*- coding: utf-8 -*-
#
# "TheVirtualBrain - Widgets" package
#
# (c) 2022-2026, TVB Widgets Team
#

import numpy as np
import pytest

from tvbwidgets.ui.dicom_widget import DicomWidget


def crosshair(plot):
    glyph = plot.figure.renderers[1].glyph
    return glyph.x, glyph.y


@pytest.mark.parametrize('size', [64, 255])
def test_sliders_work_for_any_volume_size(size):
    data = np.random.default_rng(0).random((size, size, size))
    widget = DicomWidget(data)
    last_index = size - 1

    for value in (0, last_index):
        widget.x_slider.value = value
        widget.z_slider.value = value

        assert np.array_equal(widget.axial_plot.image.data_source.data['image'][0], data[:, :, last_index - value])
        for plot in (widget.axial_plot, widget.sagittal_plot, widget.coronal_plot):
            x, y = crosshair(plot)
            assert 0 <= x <= last_index
            assert 0 <= y <= last_index

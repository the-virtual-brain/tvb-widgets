# -*- coding: utf-8 -*-
#
# "TheVirtualBrain - Widgets" package
#
# (c) 2022-2025, TVB Widgets Team
#

import numpy as np
import os
import tvbwidgets.readers as readers

TEST_DATA = os.path.join(os.path.dirname(__file__), 'data')


def test_read_edf_file():
    edf_test_file = 'test_file.edf'
    edf_path = os.path.join(TEST_DATA, edf_test_file)

    data, freq, idx = readers.read_edf_file(edf_path)
    assert data is not None
    assert freq is not None
    assert idx is not None

    assert isinstance(data, np.ndarray)
    assert data.shape == (92000, 32)

    assert isinstance(freq, float)
    assert freq == 400

    assert isinstance(idx, int)
    assert idx == 1

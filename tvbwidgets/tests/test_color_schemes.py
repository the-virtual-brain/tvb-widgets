# -*- coding: utf-8 -*-
#
# "TheVirtualBrain - Widgets" package
#
# (c) 2022-2025, TVB Widgets Team
#

import pytest
from tvbwidgets.ui.color_schemes import DEFAULT_COLOR_SCHEME, get_color_scheme, get_empty_cell_color

def test_get_color_scheme():
    assert get_color_scheme().name == DEFAULT_COLOR_SCHEME
    assert get_color_scheme("viridis").name == "viridis"
    assert get_color_scheme("rainbow4") is not None
    assert get_color_scheme("cet_rainbow4") is not None

    with pytest.raises(ValueError):
        get_color_scheme("not a colormap")

@pytest.mark.parametrize("name, expected", [
    ("turbo", "#ffffff"),
    ("Reds", "#000000"),
    ("Greys", "#ff00ff"),
])
def test_get_empty_cell_color(name, expected):
    assert get_empty_cell_color(get_color_scheme(name)) == expected
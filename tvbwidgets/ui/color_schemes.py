# -*- coding: utf-8 -*-
#
# "TheVirtualBrain - Widgets" package
#
# (c) 2022-2026, TVB Widgets Team
#

import colorcet
import matplotlib
import matplotlib.colors as mcolors
import numpy as np

DEFAULT_COLOR_SCHEME = "turbo"
EMPTY_CELL_COLORS = ("#ffffff", "#000000", "#ff00ff")
MIN_COLOR_DISTANCE = 0.3
UNKNOWN_COLOR_SCHEME_MESSAGE = ("Unknown color scheme '{}'. Use the name of a matplotlib or colorcet colormap, "
                                "e.g. 'turbo' or 'viridis'.")


def get_color_scheme(name=DEFAULT_COLOR_SCHEME):
    if name in matplotlib.colormaps:
        return matplotlib.colormaps[name]
    if name in colorcet.cm:
        return colorcet.cm[name]
    raise ValueError(UNKNOWN_COLOR_SCHEME_MESSAGE.format(name))


def get_empty_cell_color(color_scheme):
    scheme_colors = color_scheme(np.linspace(0, 1, 256))[:, :3]
    for color in EMPTY_CELL_COLORS:
        distances = np.linalg.norm(scheme_colors - mcolors.to_rgb(color), axis=1)
        if distances.min() >= MIN_COLOR_DISTANCE:
            return color
    return EMPTY_CELL_COLORS[-1]
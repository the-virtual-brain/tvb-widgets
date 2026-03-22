# -*- coding: utf-8 -*-
#
# "TheVirtualBrain - Widgets" package
#
# (c) 2022-2025, TVB Widgets Team
#

import pathlib
import numpy as np

import ipyreact
import traitlets

from .connectivity_model import ConnectivityDTO

_HERE = pathlib.Path(__file__).resolve().parent


def _to_flat_list(arr):
    """Convert numpy array to flat 1D list regardless of shape."""
    if arr is None:
        return []
    a = np.array(arr)
    return a.flatten().tolist()


def _to_list(arr):
    """Convert numpy array to list, return [] if None."""
    if arr is None:
        return []
    return np.array(arr).tolist()


class ConnectivityWidget(ipyreact.Widget):
    """
    Connectivity Edge Bundle Widget — Hybrid Canvas + SVG.
    Drop-in replacement for ConnectivityWidgetReact.
    """

    _esm = _HERE / 'connectivity_new.tsx'
    _css = (_HERE / 'connectivity_new.css').read_text()

    connectivity = traitlets.Any().tag(sync=True)

    def __init__(self, connectivity=None, **kwargs):
        if connectivity is None:
            raise ValueError("Please provide a TVB Connectivity object.")

        self.connectivity = ConnectivityDTO(
            region_labels=connectivity.region_labels.tolist(),
            weights=_to_list(connectivity.weights),
            undirected=bool(connectivity.undirected),
            tract_lengths=_to_list(connectivity.tract_lengths),
            speed=_to_flat_list(connectivity.speed),
            centres=_to_list(connectivity.centres),
            cortical=_to_flat_list(connectivity.cortical),
            hemispheres=_to_flat_list(connectivity.hemispheres),
            orientations=_to_list(connectivity.orientations),
            areas=_to_flat_list(connectivity.areas),
            # delays and idelays are (n,n) matrices — flatten to 1D for DTO
            idelays=_to_flat_list(connectivity.idelays),
            delays=_to_flat_list(connectivity.delays),
            number_of_regions=int(connectivity.number_of_regions),
            number_of_connections=int(connectivity.number_of_connections),
            parent_connectivity=connectivity.parent_connectivity,
            saved_selection=list(connectivity.saved_selection) if connectivity.saved_selection else [],
        ).trait_values()

        print(f"ConnectivityWidget ready — {connectivity.number_of_regions} regions.")
        super().__init__(**kwargs)


# Backwards-compatible alias so existing notebooks don't break
ConnectivityWidgetReact = ConnectivityWidget
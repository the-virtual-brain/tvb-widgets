# -*- coding: utf-8 -*-
#
# "TheVirtualBrain - Widgets" package
#
# (c) 2022-2025, TVB Widgets Team
#

import pathlib

import ipyreact
import traitlets
from IPython.display import HTML

from .connectivity_model import ConnectivityDTO


class ConnectivityWidgetReact(ipyreact.Widget):
    _esm = pathlib.Path(__file__).resolve().parent / 'Connectivity.tsx'
    css_rules = (pathlib.Path(__file__).resolve().parent / 'Connectivity.css').read_text()
    HTML("<style>" + css_rules + "</style>")
    connectivity = traitlets.Any().tag(sync=True)

    def __init__(self, connectivity=None, **kwargs):
        self.connectivity = ConnectivityDTO(
            region_labels=connectivity.region_labels.tolist(),
            weights=connectivity.weights.tolist(),
            undirected=connectivity.undirected,
            tract_lengths=connectivity.tract_lengths.tolist(),
            speed=connectivity.speed.tolist(),
            centres=connectivity.centres.tolist(),
            cortical=connectivity.cortical.tolist(),
            hemispheres=connectivity.hemispheres.tolist(),
            orientations=connectivity.orientations.tolist(),
            areas=connectivity.areas.tolist(),
            idelays=connectivity.idelays and connectivity.idelays.tolist(),
            delays=connectivity.delays and connectivity.delays.tolist(),
            number_of_regions=connectivity.number_of_regions,
            number_of_connections=connectivity.number_of_connections,
            parent_connectivity=connectivity.parent_connectivity,
            saved_selection=connectivity.saved_selection
        ).trait_values()
        print('init ConnectivityWidget')
        if connectivity is None:
            "Please provide a connectivity"

        super().__init__(**kwargs)

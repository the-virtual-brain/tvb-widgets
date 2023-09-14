# -*- coding: utf-8 -*-
#
# "TheVirtualBrain - Widgets" package
#
# (c) 2022-2023, TVB Widgets Team
#
import ipywidgets
import numpy
from tvb.datatypes.connectivity import Connectivity

from tvbwidgets.ui.base_widget import TVBWidget
from tvbwidgets.ui.connectivity_ipy.global_context import CONTEXT
from tvb.basic.logger.builder import get_logger

LOGGER = get_logger(__name__)


class ConnectivityOperations(ipywidgets.VBox, TVBWidget):
    def add_datatype(self, datatype):
        """
        Currently not supported
        """
        pass

    def __init__(self, **kwargs):
        super().__init__(layout={**self.DEFAULT_BORDER, 'width': '50%', 'justify-content': 'start'}, **kwargs)
        self.regions_checkboxes = []
        selector = self.__get_node_selector()
        buttons = self.__get_operations_buttons()
        history_dropdown = self.get_history_dropdown()
        children = [
            ipywidgets.HTML(
                value=f'<h3>Operations for Connectivity-{CONTEXT.connectivity.number_of_regions}</h3>'
            ),
            history_dropdown,
            selector,
            buttons]

        def update_history_ui(*args):
            children[1] = self.get_history_dropdown()
            self.children = children

        CONTEXT.observe(update_history_ui, 'connectivity')
        self.children = children

    @property
    def selected_regions(self):
        return list(map(lambda x: x.description, filter(lambda x: x.value, self.regions_checkboxes)))

    def __get_node_selector(self):
        left_children = []
        right_children = []
        region_labels = CONTEXT.connectivity.region_labels

        for region in region_labels:
            label = str(region)
            selector = ipywidgets.Checkbox(value=False, description=label, layout={'width': 'max-content'},
                                           indent=False)
            if label.startswith('l'):
                left_children.append(selector)
            else:
                right_children.append(selector)

        self.regions_checkboxes = [*left_children, *right_children]

        left = ipywidgets.VBox(children=(ipywidgets.HTML('<p>Left hemisphere</p>'),
                                         ipywidgets.VBox(children=left_children,
                                                         )),
                               layout={'width': '50%', 'align-items': 'start'}
                               )
        right = ipywidgets.VBox(children=(ipywidgets.HTML('<p>Right hemisphere</p>'),
                                          ipywidgets.VBox(children=right_children,
                                                          )),
                                layout={'width': '50%', 'align-items': 'start'}
                                )
        matrix_dropdown = ipywidgets.Dropdown(
            options=CONTEXT.MATRIX_OPTIONS,
            value=CONTEXT.matrix,
            description='Matrix:'
        )

        def on_change(value):
            CONTEXT.matrix = value['new']

        matrix_dropdown.observe(on_change, 'value')

        def on_ctx_change(value):
            matrix_dropdown.value = value

        CONTEXT.observe(on_ctx_change, 'matrix')

        container = ipywidgets.VBox(children=(matrix_dropdown,
                                              ipywidgets.HBox(children=(left, right))))
        accordion = ipywidgets.Accordion(children=[container], selected_index=None,
                                         layout={'max-height': '50vh'})
        accordion.set_title(0, 'Regions selector')
        return accordion

    def __get_operations_buttons(self):
        cut_selected_tooltip = """
        Create a new connectivity removing the selected nodes. 
        Check the selected nodes in the above dropdown to see what it is included
        """
        cut_edges_tooltip = """
        Create a new connectivity cutting the edges of selected nodes.
        Check the selected nodes in the above dropdown to see what it is included
        """
        cut_unselected_nodes = ipywidgets.Button(description='Cut selected regions',
                                                 disabled=False,
                                                 button_style='success',
                                                 tooltip=cut_selected_tooltip,
                                                 icon='scissors')

        cut_unselected_edges = ipywidgets.Button(description='Cut unselected edges',
                                                 disabled=False,
                                                 button_style='warning',
                                                 tooltip=cut_edges_tooltip,
                                                 icon='scissors')

        cut_selected_edges = ipywidgets.Button(description='Cut selected edges',
                                               disabled=False,
                                               button_style='warning',
                                               tooltip=cut_edges_tooltip,
                                               icon='scissors')

        cut_unselected_nodes.on_click(lambda *args: self.__cut_selected_nodes())
        cut_unselected_edges.on_click(lambda *args: self.__cut_edges())
        cut_selected_edges.on_click(lambda *args: self.__cut_edges(selected=True))

        return ipywidgets.HBox(children=[cut_unselected_nodes, cut_unselected_edges, cut_selected_edges])

    def __cut_selected_nodes(self):
        """
        Create a new connectivity using only the selected nodes
        """
        matrix = CONTEXT.matrix
        new_weights = CONTEXT.connectivity.weights
        new_tracts = CONTEXT.connectivity.tract_lengths if matrix == 'tracts' else None
        regions = CONTEXT.connectivity.region_labels
        selected_regions = [numpy.where(regions == label)[0][0] for label in self.selected_regions]
        new_conn = self._cut_connectivity(CONTEXT.connectivity, new_weights, selected_regions, new_tracts)
        CONTEXT.connectivity = new_conn

    def __cut_edges(self, selected=False):
        matrix = CONTEXT.matrix
        new_weights = CONTEXT.connectivity.weights
        new_tracts = CONTEXT.connectivity.tract_lengths if matrix == 'tracts' else None
        regions = CONTEXT.connectivity.region_labels
        selected_regions = [numpy.where(regions == label)[0][0] for label in self.selected_regions]
        new_conn = self._cut_connectivity_edges(CONTEXT.connectivity, new_weights, selected_regions, new_tracts,
                                                selected)
        CONTEXT.connectivity = new_conn

    def _reorder_arrays(self, original_conn, new_weights, interest_areas, new_tracts=None):
        """
        Returns ordered versions of the parameters according to the hemisphere permutation.
        """
        permutation = original_conn.hemisphere_order_indices
        inverse_permutation = numpy.argsort(permutation)  # trick to invert a permutation represented as an array
        interest_areas = inverse_permutation[interest_areas]
        # see :meth"`ordered_weights` for why [p:][:p]
        new_weights = new_weights[inverse_permutation, :][:, inverse_permutation]

        if new_tracts is not None:
            new_tracts = new_tracts[inverse_permutation, :][:, inverse_permutation]

        return new_weights, interest_areas, new_tracts

    def get_history_dropdown(self):
        values = [(conn.gid.hex, conn) for conn in CONTEXT.connectivities_history]

        dropdown = ipywidgets.Dropdown(options=values,
                                       description='View history',
                                       disabled=False)
        dropdown.observe(lambda x: print(x['new']), 'value')
        return dropdown

    def _cut_connectivity_edges(self, original_conn, new_weights, interest_areas,
                                new_tracts=None, selected=False):
        # type: (Connectivity, numpy.array, numpy.array, numpy.array) -> Connectivity
        """
        Generate new Connectivity based on a previous one, by changing weights (e.g. simulate lesion).
        The returned connectivity has the same number of nodes. The edges of unselected nodes will have weight 0.
        :param original_conn: Original Connectivity, to copy from
        :param new_weights: weights matrix for the new connectivity
        :param interest_areas: ndarray of the selected node id's
        :param new_tracts: tracts matrix for the new connectivity
        :param selected: if true cuts out edges of selected areas else unselected edges
        """
        if not len(interest_areas):
            LOGGER.error('No intrest areas selected!')
            return CONTEXT.connectivity

        new_weights, interest_areas, new_tracts = self._reorder_arrays(original_conn, new_weights,
                                                                       interest_areas, new_tracts)
        if new_tracts is None:
            new_tracts = original_conn.tract_lengths

        for i in range(len(original_conn.weights)):
            for j in range(len(original_conn.weights)):
                if i not in interest_areas or j not in interest_areas:
                    if not selected:
                        new_weights[i][j] = 0
                elif i in interest_areas or j in interest_areas and selected:
                    new_weights[i][j] = 0

        final_conn = Connectivity()
        final_conn.parent_connectivity = original_conn.gid.hex
        final_conn.saved_selection = interest_areas.tolist()
        final_conn.weights = new_weights
        final_conn.centres = original_conn.centres
        final_conn.region_labels = original_conn.region_labels
        final_conn.orientations = original_conn.orientations
        final_conn.cortical = original_conn.cortical
        final_conn.hemispheres = original_conn.hemispheres
        final_conn.areas = original_conn.areas
        final_conn.tract_lengths = new_tracts
        final_conn.configure()
        return final_conn

    def _cut_connectivity(self, original_conn, new_weights, interest_areas, new_tracts=None):
        # type: (Connectivity, numpy.array, numpy.array, numpy.array) -> Connectivity
        """
        Generate new Connectivity object based on current one, by removing nodes (e.g. simulate lesion).
        Only the selected nodes will get used in the result. The order of the indices in interest_areas matters.
        If indices are not sorted then the nodes will be permuted accordingly.

        :param original_conn: Original Connectivity(HasTraits), to cut nodes from
        :param new_weights: weights matrix for the new connectivity
        :param interest_areas: ndarray with the selected node id's.
        :param new_tracts: tracts matrix for the new connectivity
        """
        if not len(interest_areas):
            LOGGER.error('No interest areas selected!')
            return CONTEXT.connectivity

        new_weights, interest_areas, new_tracts = self._reorder_arrays(original_conn, new_weights,
                                                                       interest_areas, new_tracts)
        if new_tracts is None:
            new_tracts = original_conn.tract_lengths[interest_areas, :][:, interest_areas]
        else:
            new_tracts = new_tracts[interest_areas, :][:, interest_areas]
        new_weights = new_weights[interest_areas, :][:, interest_areas]

        final_conn = Connectivity()
        final_conn.parent_connectivity = None
        final_conn.weights = new_weights
        final_conn.centres = original_conn.centres[interest_areas, :]
        final_conn.region_labels = original_conn.region_labels[interest_areas]
        if original_conn.orientations is not None and len(original_conn.orientations):
            final_conn.orientations = original_conn.orientations[interest_areas, :]
        if original_conn.cortical is not None and len(original_conn.cortical):
            final_conn.cortical = original_conn.cortical[interest_areas]
        if original_conn.hemispheres is not None and len(original_conn.hemispheres):
            final_conn.hemispheres = original_conn.hemispheres[interest_areas]
        if original_conn.areas is not None and len(original_conn.areas):
            final_conn.areas = original_conn.areas[interest_areas]
        final_conn.tract_lengths = new_tracts
        final_conn.saved_selection = []
        final_conn.configure()
        return final_conn

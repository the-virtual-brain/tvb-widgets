# -*- coding: utf-8 -*-
#
# "TheVirtualBrain - Widgets" package
#
# (c) 2022-2023, TVB Widgets Team
#
import ipywidgets
from tvbwidgets.ui.base_widget import TVBWidget
from tvbwidgets.ui.connectivity_ipy.global_context import CONTEXT


class ConnectivityOperations(ipywidgets.VBox, TVBWidget):
    def add_datatype(self, datatype):
        """
        Currently not supported
        """
        pass

    def __init__(self, connectivity, **kwargs):
        super().__init__(layout={**self.DEFAULT_BORDER, 'width': '50%', 'justify-content': 'start'}, **kwargs)
        self.connectivity = connectivity
        self.regions_checkboxes = []
        selector = self.__get_node_selector()
        buttons = self.__get_operations_buttons()
        children = [
            ipywidgets.HTML(
                value=f'<h3>Operations for Connectivity-{connectivity.number_of_regions}</h3>'
            ), selector, buttons]
        self.children = children

    def __get_node_selector(self):
        left_children = []
        right_children = []
        region_labels = self.connectivity.region_labels

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

    @property
    def selected_regions(self):
        print(self.regions_checkboxes)
        return list(map(lambda x: x.description, filter(lambda x: x.value, self.regions_checkboxes)))

    def __get_operations_buttons(self):
        cut_selected_tooltip = """
        Create a new connectivity removing the selected nodes. 
        Check the selected nodes in the above dropdown to see what it is included
        """
        cut_edges_tooltip = """
        Create a new connectivity cutting the edges of selected nodes.
        Check the selected nodes in the above dropdown to see what it is included
        """
        cut_selected = ipywidgets.Button(description='Cut selected regions',
                                         disabled=False,
                                         button_style='success',
                                         tooltip=cut_selected_tooltip,
                                         icon='scissors')

        cut_edges_of_selected = ipywidgets.Button(description='Cut edges of selected',
                                                  disabled=False,
                                                  button_style='warning',
                                                  tooltip=cut_edges_tooltip,
                                                  icon='scissors')

        cut_selected.on_click(lambda *args: self.__cut_selected_nodes())
        cut_edges_of_selected.on_click(lambda *args: self.__cut_selected_edges())

        return ipywidgets.HBox(children=[cut_selected, cut_edges_of_selected])

    def __cut_selected_nodes(self):
        print('cutting selected: ', self.selected_regions)

    def __cut_selected_edges(self):
        print('cutting edges: ', self.selected_regions)

    def __cut_incoming_edges(self):
        pass

    def _cut_outgoing_edges(self):
        pass

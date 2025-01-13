# -*- coding: utf-8 -*-
#
# "TheVirtualBrain - Widgets" package
#
# (c) 2022-2025, TVB Widgets Team
#

import os.path
import plotly.graph_objects as go
import ipywidgets as widgets
from IPython.core.display_functions import display
from tvbwidgets.core.exceptions import InvalidInputException
from tvbwidgets.core.pse.pse_data import PSEData, PSEStorage
from tvbwidgets.ui.base_widget import TVBWidget


class PSEWidget(TVBWidget):
    """Visualize PSE results"""

    def __init__(self, file_name, **kwargs):
        # type: (str, dict) -> None
        """
        :param file_name: path to the file_name that contains the data necessary for the visualization
        """
        super().__init__(**kwargs)
        if not os.path.exists(file_name):
            raise InvalidInputException(f"File {file_name} was not found!")
        self.file_name = file_name
        self.param1_title = None
        self.param2_title = None
        self.param1_value = None
        self.param2_value = None
        self.data = None
        self.metrics_names = []
        self.dict_metrics = {}
        self.figure = None
        self.smooth_effect_cb = None
        self.change_color_dd = None
        self.metrics_change_dd = None
        self.read_h5_file()
        self._map_names_to_metrics()
        self._create_visualizer()

    def read_h5_file(self):
        pse_result = PSEData()
        PSEStorage(self.file_name).load_into(pse_result)
        self.param1_title = pse_result.x_title
        self.param2_title = pse_result.y_title
        self.param1_value = pse_result.x_value
        self.param2_value = pse_result.y_value
        self.metrics_names = pse_result.metrics_names
        self.data = pse_result.results

    def _map_names_to_metrics(self):
        for index in range(self.metrics_names.__len__()):
            self.dict_metrics[self.metrics_names[index]] = self.data[index]

    def _create_visualizer(self):
        self.param1_value = [str(elem) for elem in self.param1_value]
        self.param2_value = [str(elem) for elem in self.param2_value]
        pse_layout = go.Layout(width=900, height=600,
                               xaxis=go.layout.XAxis(linecolor='black', linewidth=1, mirror=True,
                                                     title=self.param2_title),
                               yaxis=go.layout.YAxis(linecolor='black', linewidth=1, mirror=True,
                                                     title=self.param1_title),
                               margin=go.layout.Margin(l=80, r=50, b=50, t=80, pad=4), title="PSE Visualizer",
                               titlefont=dict(size=20, family='Arial, sans-serif'), )
        self.figure = go.FigureWidget(layout=pse_layout)

        self.figure.add_trace(go.Heatmap(z=list(self.dict_metrics.values())[0], x=self.param2_value,
                                         y=self.param1_value, colorscale='RdBu', connectgaps=False,
                                         showscale=True, zsmooth=False))

        self._populate_features()

    def _populate_features(self):
        self._smooth_effect()
        self._colors_options()
        self._metrics_options()
        features_vbox = widgets.VBox(children=[self.smooth_effect_cb, self.change_color_dd, self.metrics_change_dd])
        features_accordion = widgets.Accordion(children=[features_vbox], selected_index=0,
                                               layout=widgets.Layout(width='27%', top='80px'))
        features_accordion.set_title(0, 'Features')
        table = widgets.HBox([self.figure, features_accordion], layout=self.DEFAULT_BORDER)
        display(table)

    def _smooth_effect(self):
        self.smooth_effect_cb = widgets.Checkbox(value=False, description='Smooth visualizer',
                                                 layout=widgets.Layout(margin='10px 0px 10px 0px'))

        def smooth_effect_changed(change):
            if change['type'] != 'change' or change['name'] != 'value':
                return

            if change['new']:
                effect = 'best'
            else:
                effect = False
            self.figure.update_traces(go.Heatmap(zsmooth=effect))

        self.smooth_effect_cb.observe(smooth_effect_changed)

    def _colors_options(self):
        self.change_color_dd = widgets.Dropdown(
            options=['Blackbody', 'Earth', 'Jet', 'Picnic', 'RdBu', 'Rainbow'],
            description="Color:",
            value='RdBu',
            disabled=False)

        def color_changed(change):
            if change['type'] != 'change' or change['name'] != 'value':
                return

            self.figure.update_traces(go.Heatmap(colorscale=change['new']))

        self.change_color_dd.observe(color_changed)

    def _metrics_options(self):
        self.metrics_change_dd = widgets.Dropdown(
            options=self.metrics_names,
            description="Metric:",
            value=list(self.dict_metrics.keys())[0],
            disabled=False)

        def metric_changed(change):
            if change['type'] != 'change' or change['name'] != 'value':
                return

            self.figure.update_traces(go.Heatmap(name=change['new'], z=self.dict_metrics[change['new']]))

        self.metrics_change_dd.observe(metric_changed)

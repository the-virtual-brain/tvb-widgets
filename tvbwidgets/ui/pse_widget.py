# -*- coding: utf-8 -*-
#
# "TheVirtualBrain - Widgets" package
#
# (c) 2022-2023, TVB Widgets Team
#

import plotly.graph_objects as go
import ipywidgets as widgets
import numpy as np
from IPython.core.display_functions import display
from tvbwidgets.ui.base_widget import TVBWidget


class PSEWidget(TVBWidget):
    """Visualize PSE results"""

    def __init__(self, data, x_title, y_title, x_value, y_value, metrics_names, **kwargs):
        # type: (np.ndarray, str, str, list, list, list, dict) -> None
        """
        :param data: Numpy array with metrics data
        :param x_title: Title of X axis
        :param y_title: Title of Y axis
        :param x_value: List consists of X axis range(min, max) and a step, ex: [0, 30, 2]
        :param y_value: List consists of Y axis range(min, max) and a step
        :param metrics_names: Representative names for each metrics
        """
        super().__init__(**kwargs)
        self.x_title = x_title
        self.y_title = y_title
        self.x_value = x_value
        self.y_value = y_value
        self.data = data
        self.metrics_names = metrics_names
        self.dict_metrics = {}
        self.figure = None
        self.smooth_effect_cb = None
        self.change_color_dd = None
        self.metrics_change_dd = None
        self._map_names_to_metrics()
        self._create_visualizer()

    def _map_names_to_metrics(self):
        for index in range(self.metrics_names.__len__()):
            self.dict_metrics[self.metrics_names[index]] = self.data[index]

    def _create_visualizer(self):
        pse_layout = go.Layout(width=1000, height=500,
                               xaxis=go.layout.XAxis(linecolor='black', linewidth=1, mirror=True, title=self.x_title,
                                                     range=[self.x_value[0], self.x_value[1]], dtick=self.x_value[2]),
                               yaxis=go.layout.YAxis(linecolor='black', linewidth=1, mirror=True, title=self.y_title,
                                                     range=[self.y_value[0], self.y_value[1]], dtick=self.y_value[2]),
                               margin=go.layout.Margin(
                                   l=100,
                                   r=50,
                                   b=100,
                                   t=100,
                                   pad=4), title="PSE Visualizer", titlefont=dict(size=20, family='Arial, sans-serif'),
                               )
        self.figure = go.FigureWidget(layout=pse_layout)
        self.figure.add_trace(go.Heatmap(z=list(self.dict_metrics.values())[0], colorscale='RdBu', showscale=True,
                                         zsmooth='best'))
        self._populate_features()

    def _populate_features(self):
        self._smooth_effect()
        self._colors_options()
        self._metrics_options()
        features_vbox = widgets.VBox(children=[self.smooth_effect_cb, self.change_color_dd,
                                               self.metrics_change_dd])
        features_accordion = widgets.Accordion(children=[features_vbox], selected_index=None,
                                               layout=widgets.Layout(width='25%', marginTop='100px'))
        features_accordion.set_title(0, 'Features')
        table = widgets.HBox([features_accordion, self.figure], layout=self.DEFAULT_BORDER)
        display(table)

    def _smooth_effect(self):
        self.smooth_effect_cb = widgets.Checkbox(True, description='Smooth visualizer',
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

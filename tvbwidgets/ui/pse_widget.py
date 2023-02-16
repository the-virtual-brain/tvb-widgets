import plotly.graph_objects as go
import numpy as np
import ipywidgets as widgets
from IPython.core.display_functions import display


class PSEWidget:
    """Visualize PSE results"""

    def __init__(self):
        self.data = None
        self.layout = None
        self.figure = None
        self.smooth_effect = False
        self.smooth_effect_checkbox = None
        self.change_color_dropdown = None
        self._create_visualizer()
        self._populate_features()

    def _populate_visualizer(self):
        # TODO : The visualizer will be populated with the resulted matrix/es from PSE launcher
        self.data = np.random.rand(50, 50)

    def _create_visualizer(self):
        self.layout = go.Layout(width=1000, height=500,
                                xaxis=go.layout.XAxis(linecolor='black', linewidth=1, mirror=True),
                                yaxis=go.layout.YAxis(linecolor='black', linewidth=1, mirror=True),
                                margin=go.layout.Margin(
                                    l=100,
                                    r=50,
                                    b=100,
                                    t=100,
                                    pad=4), title="PSE Visualizer", titlefont=dict(size=20,
                                                                                   family='Arial, sans-serif'),
                                )
        self.figure = go.FigureWidget(layout=self.layout)
        self._populate_visualizer()
        self.figure.add_trace(go.Heatmap(z=self.data, colorscale='RdBu', showscale=True))

    def _populate_features(self):
        self._smooth_effect()
        self._color_changed()
        features = widgets.VBox(children=[self.smooth_effect_checkbox, self.change_color_dropdown])
        features_area = widgets.Accordion(children=[features], selected_index=None,
                                          layout=widgets.Layout(width='25%', marginTop='100px'))
        features_area.set_title(0, 'Features')
        table = widgets.HBox([features_area, self.figure])
        display(table)

    def _smooth_effect(self):
        self.smooth_effect_checkbox = widgets.Checkbox(False, description='Smooth visualizer',
                                                       layout=widgets.Layout(margin='10px 0px 10px 0px'))

        def smooth_effect_changed(change):
            if change['type'] != 'change' or change['name'] != 'value':
                return

            if change['new']:
                self.smooth_effect = 'best'
            else:
                self.smooth_effect = False
            self.figure.update_traces(go.Heatmap(z=self.data, showscale=True, zsmooth=self.smooth_effect))

        self.smooth_effect_checkbox.observe(smooth_effect_changed)

    def _color_changed(self):
        self.change_color_dropdown = widgets.Dropdown(
            options=['Blackbody', 'Cividis', 'Earth', 'RdBu', 'Rainbow', 'Viridis', 'YlGnBu', 'YlOrRd'],
            description="Color:",
            value='RdBu',
            disabled=False)

        def change_color(change):
            if change['type'] != 'change' or change['name'] != 'value':
                return

            self.figure.update_traces(go.Heatmap(z=self.data, showscale=True, colorscale=change['new']))

        self.change_color_dropdown.observe(change_color)


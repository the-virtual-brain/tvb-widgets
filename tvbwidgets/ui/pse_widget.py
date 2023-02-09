import plotly.graph_objects as go
import numpy as np
import ipywidgets as widgets
from IPython.core.display_functions import display
from IPython.core.display_functions import clear_output
import plotly.offline as ofl


class PSEWidget:
    """Visualize PSE results"""

    def __init__(self):
        self.data = None
        self.layout = None
        self.figure = None
        self.smoothFunct = False
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
                                    pad=4), title="Visualizer PSE", titlefont=dict(size=20,
                                                                                   family='Arial, sans-serif'),
                                )
        self.figure = go.FigureWidget(layout=self.layout)
        self._populate_visualizer()
        self.figure.add_trace(go.Heatmap(z=self.data, showscale=True))

    def _populate_features(self):
        smooth_viz = widgets.Checkbox(False, description='Smooth visualizer')
        smooth_viz.observe(self._change_smooth_effect, names="value", type="change")
        features_area = widgets.Accordion(children=[smooth_viz], selected_index=None,
                                          layout=widgets.Layout(width='25%', marginTop='100px'))
        features_area.set_title(0, 'Features')
        table = widgets.HBox([self.figure, features_area])
        display(table)

    def _change_smooth_effect(self, value):
        if value['new']:
            self.smoothFunct = 'best'
        else:
            self.smoothFunct = False
        self.redraw()

    def redraw(self):
        self.figure.update_traces(go.Heatmap(z=self.data, showscale=True, zsmooth=self.smoothFunct))

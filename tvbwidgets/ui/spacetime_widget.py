import io
import numpy as np
import pythreejs as p3
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.gridspec import GridSpec
from IPython.display import display
from tvb.datatypes.connectivity import Connectivity
from tvbwidgets.ui.base_widget import TVBWidget
from ipywidgets import Tab, Output, HBox, BoundedFloatText, FloatText, Layout


class SpaceTimeVisualizerWidget(TVBWidget):
    def __init__(self, connectivity, width=600, height=400, **kwargs):
        style = self.DEFAULT_BORDER
        super().__init__(**kwargs, layout=style)
        self.view_width = width
        self.view_height = height
        self.connectivity = connectivity
        self.add_options()
        self.conduction_speed = self.options.children[0].value
        self.from_time = self.options.children[1].value
        self.to_time =  self.options.children[2].value
        self.num_slices = 6
        self._prepare_tab()

    def _prepare_tab(self):
        self.tab = Tab()
        self._prepare_scene()

        self.graphs_pythreejs = Output()
        with self.graphs_pythreejs:
            display(self.renderer)

        self.graphs_matplotlib = Output()
        self.create_matplotlib_graphs()
        with self.graphs_matplotlib:
            display(self.fig)

        self.tab.children = [self.graphs_pythreejs, self.graphs_matplotlib]
        
    def _prepare_scene(self):
        self.camera = p3.PerspectiveCamera(position=[23, 7, -6], aspect=2)
        self.light = p3.AmbientLight()
        self.key_light = p3.DirectionalLight(position=[0, 10, 10])
        self.scene = p3.Scene()
        self.scene.add([self.camera, self.key_light, self.light])
        self.scene.background = None
        self._prepare_slices()
        self.controls = p3.OrbitControls(controlling=self.camera)
        self.renderer = p3.Renderer(camera=self.camera, scene=self.scene, controls=[self.controls],
                                    width=self.view_width, height=self.view_height)
        
    def _prepare_slices(self):
        total_slices = self.num_slices+1
        self.graph_slices = []
        for i in range(total_slices):
            graph_slice = self._create_graph_slice(i)
            self.scene.add(graph_slice)
            self.graph_slices.append(graph_slice)

    def _create_graph_slice(self, i):
        z_coordinate = -i * 2.5 + 15
        return p3.Mesh(
            p3.BoxBufferGeometry(width=7, height=7, depth=0.1),
            p3.MeshPhysicalMaterial(map=self._generate_texture(i)),
            position=[10, 1, z_coordinate]
        )

    def _generate_texture(self, i):
        connectivity = self._prepare_connectivity(i)
        texture = p3.DataTexture(
            data=self._generate_colors(connectivity),
            format="RGBFormat",
            type="FloatType"
        )
        return texture

    def _generate_colors(self, connectivity):
        colors = [
            '#000088', '#4d1c34', '#7a3282', '#8ea674', '#27913c', '#1c464a',
            '#247663', '#38bcaa', '#a9e9ff', '#5fcdfc', '#36a0c1', '#f99e2c',
            '#fc5326', '#df0537'
        ]
        color_scheme = mcolors.LinearSegmentedColormap.from_list('color_scheme', colors)
        norm = mcolors.Normalize(vmin=0, vmax=3)
        color_data = color_scheme(norm(connectivity))[:, :, :3]
        
        # Generate grid lines
        repetition_pattern = np.ones((5, 5, 1))
        color_data = np.kron(color_data, repetition_pattern)
        size = color_data.shape[0]
        mask = (np.arange(size) % 5 == 0)[:, None] | (np.arange(size) % 5 == 0)[None, :]
        color_data[mask] = [0, 0, 0]
        
        return color_data

    def _prepare_connectivity(self, i):
        """Prepares data for different slices."""
        if i == 0:
            connectivity = self.connectivity.weights
        else:
            slice_range = ((self.to_time-self.from_time) * i) / self.num_slices
            prev_slice_range =  ((self.to_time-self.from_time) * (i - 1)) / self.num_slices
            time_delay = self.connectivity.tract_lengths * self.conduction_speed
            mask = (time_delay < slice_range) & (time_delay > prev_slice_range) 
            connectivity = np.where(mask, self.connectivity.weights, 0)
        return connectivity
    
    def create_matplotlib_graphs(self):
        self.fig = plt.figure(figsize=(14, 10))
        self.ims = []
        gs = GridSpec(3, 4, figure = self.fig)
        
        for i in range(self.num_slices + 1):
            position = gs[int(i/3), int(i%3)]
            ax = self.fig.add_subplot(position)
            connectivity = self._prepare_connectivity(i)
            colors = self._generate_colors(connectivity)
            ax.imshow(colors)
            ax.set_xticks([]) 
            ax.set_yticks([])
            self.ims.append(ax)
         
        self.fig.subplots_adjust(left=0, right=1, top=1, bottom=0, wspace=0.01, hspace=0.01)
        plt.close(self.fig)     

    def add_options(self):
        self.options = HBox(layout = Layout(width = '500px'))
        self.option_conduction_speed = FloatText(
                value=1.0,
                step=0.1,
                layout=Layout(width='150px'), 
                style={'description_width': 'initial'},
                description='Conduction Speed:',
                disabled=False
                )
        self.option_conduction_speed.observe(self.on_change,names = "value")
        self.option_from_time = BoundedFloatText(
                    value=0.0,
                    min=0.0,
                    max=153.49,
                    step=0.1,
                    layout=Layout(width='150px'), 
                    description='from[ms]:',
                    disabled=False
                )
        self.option_from_time.observe(self.on_change,names = "value")
        self.option_to_time = BoundedFloatText(
                    value= 153.49,
                    min=0.0,
                    max=153.49,
                    step=0.1,
                    layout=Layout(width='150px'), 
                    description='to[ms]:',
                    disabled=False
                )
        self.option_to_time.observe(self.on_change,names = "value")
        self.options.children = [self.option_conduction_speed, self.option_from_time, self.option_to_time]

    def on_change(self,change):
        self.graphs_matplotlib.clear_output()
        self.conduction_speed = self.options.children[0].value
        self.from_time = self.options.children[1].value
        self.to_time =  self.options.children[2].value

        for i in range(len(self.graph_slices)):
            connectivity = self._prepare_connectivity(i)
            data = self._generate_colors(connectivity)
            self.graph_slices[i].material.map.data = data
            self.ims[i].imshow(data)

        with self.graphs_matplotlib:
            display(self.fig)

    def display(self):
        display(self.options)
        display(self.tab)

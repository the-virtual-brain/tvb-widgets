# -*- coding: utf-8 -*-
#
# "TheVirtualBrain - Widgets" package
#
# (c) 2022-2025, TVB Widgets Team
#
"""
..moduleauthor:: Priya Yadav 
<priyayadav012004@gmail.com>
"""

import math
import numpy as np
import pythreejs as p3
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.gridspec import GridSpec
from IPython.display import display
from tvbwidgets.ui.base_widget import TVBWidget
from ipywidgets import Tab, Output, HBox, BoundedFloatText, HTML, Text, Layout


class SpaceTimeVisualizerWidget(TVBWidget):
    def __init__(self, connectivity, width=900, height=600, **kwargs):
        style = self.DEFAULT_BORDER
        super().__init__(**kwargs, layout=style)
        self.view_width = width
        self.view_height = height
        self.connectivity = connectivity
        colors = [
            '#000033', '#4d1c34', '#7a3282', '#8ea674', '#27913c', '#1c464a',
            '#247663', '#38bcaa', '#a9e9ff', '#5fcdfc', '#36a0c1', '#f99e2c',
            '#fc5326', '#df0537'
        ]
        self.color_scheme = mcolors.LinearSegmentedColormap.from_list('color_scheme', colors)
        self.norm = mcolors.Normalize(vmin=0, vmax=3)
    
        self._add_options()
        self.conduction_speed = self.options.children[0].value
        self.from_time = self.options.children[1].value
        self.to_time =  self.options.children[2].value
        self.num_slices = 6
        self.picked_slice = None
        self._prepare_widget()

    def _prepare_widget(self):
        self.hbox = HBox(layout = self.DEFAULT_BORDER)
        self.tab = Tab(layout = self.DEFAULT_BORDER)
        self._prepare_scene()

        self.graphs_pythreejs = Output()
        with self.graphs_pythreejs:
            display(self.renderer)

        self.graphs_matplotlib = Output()
        self._create_matplotlib_graphs()
        with self.graphs_matplotlib:
            display(self.fig)

        self.tab.children = [self.graphs_pythreejs, self.graphs_matplotlib]
        self.tab.set_title(0, "Interactive Viewer")
        self.tab.set_title(1, "Plots Overview")

        self._prepare_plot_details()
        self.hbox.children = [self.tab, self.plot_details]

    def _prepare_scene(self):
        self.camera = p3.PerspectiveCamera(position=[30, 0, 11], aspect=2)
        self.light = p3.AmbientLight(intensity=2)
        self.key_light = p3.DirectionalLight(position=[30, 0, 0], intensity=5)
        self.scene = p3.Scene()
        self.scene.add([self.camera, self.key_light, self.light])
        self.scene.background = None
        self._prepare_slices()
        self._prepare_grid()
        self.scene.add(self.grid)
        self.grid.visible = False
        self.controls = p3.OrbitControls(controlling=self.camera)
        self.controls.enabled = False
        self.picker = p3.Picker(controlling = self.scene, event = "click")
        self.picker.observe(self.on_pick, names = ["point"])
        self.renderer = p3.Renderer(camera=self.camera, scene=self.scene, controls=[self.picker],
                                    width=self.view_width, height=self.view_height)
    
    def _prepare_slices(self):
        total_slices = self.num_slices + 1
        self.graph_slices = []
        for i in range(total_slices):
            graph_slice = self._create_graph_slice(i)
            graph_slice.material.map = self._generate_texture(i)
            graph_slice.rotateY(math.radians(180))
            self.scene.add([graph_slice])
            self.graph_slices.append(graph_slice)
          

    def _create_graph_slice(self, i):
        z_coordinate = -i*3 + 14 if i == 0 else -i*2 + 11 - 0.1*i*i
        return p3.Mesh(
            p3.BoxBufferGeometry(width=7, height=7, depth=0.1),
            p3.MeshPhysicalMaterial(),
            position=[16, 0, z_coordinate],
            name=f"{i}"
        )

    def _generate_texture(self, i):
        connectivity = self._prepare_connectivity(i)
        color_data=self._generate_colors(connectivity)
        color_data = np.fliplr(color_data)

        texture = p3.DataTexture(
            data = color_data,
            format="RGBFormat",
            type="FloatType"
        )
        return texture

    def _generate_colors(self, connectivity):
        color_data = self.color_scheme(self.norm(connectivity))[:, :, :3]
        return color_data
    
    def _prepare_grid(self):
        grid_tex = self._generate_gridlines()
        self.grid = self._create_graph_slice(3)
        self.grid.material.map = grid_tex
        self.grid.material.transparent = True
        self.grid.position = [0, 0, 0]
        self.grid.name = "grid"
        self.grid.scale = [4, 3, 1]
        self.grid.lookAt(self.camera.position)
    
    def _generate_gridlines(self):
        grid = np.zeros((76, 76, 4))
        repetition_pattern = np.ones((5, 5, 1))
        grid = np.kron(grid, repetition_pattern)
        size = grid.shape[0]
        mask = (np.arange(size) % 5 == 0)[:, None] | (np.arange(size) % 5 == 0)[None, :]
        grid[mask] = [0, 0, 0, 1]
        
        grid_texture = p3.DataTexture(
            data=grid,
            format="RGBAFormat",
            type="FloatType"
        )
        return grid_texture

    def _prepare_connectivity(self, i):
        """Prepares data for different slices."""
        self.intervals = np.linspace(self.from_time, self.to_time, self.num_slices+1 )
        if i == 0:
            slice_range = self.to_time
            prev_slice_range = self.from_time
        else:
            slice_range = self.intervals[i]        
            prev_slice_range = self.intervals[i-1]   
        time_delay = self.connectivity.tract_lengths / self.conduction_speed
        mask = (time_delay <= slice_range) & (time_delay >= prev_slice_range) 
        connectivity = np.where(mask, self.connectivity.weights, 0)
        return connectivity
    
    def _create_matplotlib_graphs(self):
        self.fig = plt.figure(figsize=(self.view_width/75.65, self.view_height/75.65))
        self.ims = []
        gs = GridSpec(3, 4, figure = self.fig)
        n = self.connectivity.weights.shape[0]
        
        for i in range(self.num_slices + 1):
            position = gs[int(i/3), int(i%3)]
            ax = self.fig.add_subplot(position)
            connectivity = self._prepare_connectivity(i)
            colors = self._generate_colors(connectivity)
            ax.imshow(colors)
            ax.set_xticks(np.arange(0, n, 5))
            ax.set_yticks(np.arange(0, n, 5))
            ax.tick_params(axis="both", labelsize = 6)
            self.ims.append(ax)
         
        self.fig.subplots_adjust(left=0, right=1, top=1, bottom=0, wspace=0.1, hspace=0.1)
        plt.close(self.fig)      

    def _add_options(self):
        self.options = HBox(layout = self.DEFAULT_BORDER)
        max_time = self.connectivity.tract_lengths.max() 
        min_time = self.connectivity.tract_lengths.min() 
        self.option_conduction_speed = BoundedFloatText(
                value=1.0,
                min=0.1,
                max=round(self.connectivity.tract_lengths.max(), 2),
                step=0.1,
                layout=Layout(width='170px'), 
                style={'description_width': 'initial'},
                description='Conduction Speed:',
                disabled=False
                )
        self.option_conduction_speed.observe(self.on_change,names = "value")
        self.option_from_time = BoundedFloatText(
                    value=min_time,
                    min=min_time,
                    max=max_time,
                    step=0.1,
                    layout=Layout(width='160px'), 
                    description='from[ms]:',
                    disabled=False
                )
        self.option_from_time.observe(self.on_change,names = "value")
        self.option_to_time = BoundedFloatText(
                    value= max_time,
                    min=min_time,
                    max=max_time,
                    step=0.1,
                    layout=Layout(width='160px'), 
                    description='to[ms]:',
                    disabled=False
                )
        self.option_to_time.observe(self.on_change,names = "value")
        self.selection = Text(
                                    value = "None",
                                    description = "selection[ms]:",
                                    layout = Layout(width = "200px")
                                     )
        self.options.children = [self.option_conduction_speed, self.option_from_time, self.option_to_time, self.selection]

    def on_change(self, change):
        self.graphs_matplotlib.clear_output()
        self.conduction_speed = self.options.children[0].value
        if change["owner"].description == "Conduction Speed:":
            self.options.children[1].max = self.connectivity.tract_lengths.max() / self.conduction_speed
            self.options.children[2].max = self.connectivity.tract_lengths.max() / self.conduction_speed
            self.options.children[1].min = self.connectivity.tract_lengths.min() / self.conduction_speed
            self.options.children[2].min = self.connectivity.tract_lengths.min() / self.conduction_speed
            self.options.children[1].value = self.options.children[1].min 
            self.options.children[2].value = self.options.children[2].max
        self.from_time = self.options.children[1].value
        self.to_time =  self.options.children[2].value
        self.plot_details.value = self._generate_details()

        for i in range(len(self.graph_slices)):
            connectivity = self._prepare_connectivity(i)
            data = self._generate_colors(connectivity)
            self.graph_slices[i].material.map.data = np.fliplr(data)
            self.ims[i].imshow(data)

        with self.graphs_matplotlib:
            display(self.fig)

    def on_pick(self, change):
        picked_slice = self.picker.object
        if picked_slice is not None:
            if picked_slice != self.picked_slice and picked_slice.name != "grid":
                self._handle_new_pick(picked_slice)
            else:
                self._handle_existing_pick(picked_slice)

    def _handle_new_pick(self, picked_slice):
        for i in range(len(self.graph_slices)):
            self.graph_slices[i].visible = False
        self.picked_slice = picked_slice
        self.pos = self.picked_slice.position
        picked_slice.position = [0, 0, 0]
        picked_slice.scale = [4, 3, 1]
        picked_slice.lookAt(self.camera.position)
        picked_slice.visible = True
        self.grid.visible = True
        self.light.intensity = 3
        self.key_light.intensity = 0
        i = int(picked_slice.name)
        if i == 0:
            self.selection.value = f"{self.intervals[0]:.2f} .. {self.intervals[-1]:.2f}"
        else:
            self.selection.value = f"{self.intervals[i - 1]:.2f} .. {self.intervals[i]:.2f}"

    def _handle_existing_pick(self, picked_slice):
        if picked_slice.name == "grid":
            picked_slice = self.picked_slice
        for i in range(7):
            self.graph_slices[i].visible = True
        picked_slice.position = self.pos
        picked_slice.scale = [1, 1, 1]
        picked_slice.rotateY(math.radians(110))
        self.grid.visible = False
        self.picked_slice = None
        self.light.intensity = 2
        self.key_light.intensity = 5
        self.selection.value = "None"

    def _prepare_plot_details(self):
        self.plot_details = HTML(
                            value = self._generate_details(),
                            layout = self.DEFAULT_BORDER
                            )

    def _generate_details(self):
        return f"""<br>
            <div style="line-height:1px;">
            <br><h3>PLOT DETAILS</h3> <br><br>
            <h4>conduction speed:</h4><br> 
            {self.conduction_speed} mm/ms<br>
            <h4>min(non-zero) </h4><h4>delay: </h4><br>
            {np.min(self.connectivity.tract_lengths[np.nonzero(self.connectivity.tract_lengths)])/self.conduction_speed} ms<br>
            <h4>max delay: </h4><br>
            {np.max(self.connectivity.tract_lengths)/self.conduction_speed} ms<br>
            <h4>min(non-zero) </h4><h4>tract length:</h4> <br>
            {np.min(self.connectivity.tract_lengths[np.nonzero(self.connectivity.tract_lengths)])} mm<br>
            <h4>max tract length: </h4><br>
            {np.max(self.connectivity.tract_lengths,)} mm<br>
            <h4>min(non-zero) </h4><h4>weight: </h4><br>
            {np.min(self.connectivity.weights[np.nonzero(self.connectivity.weights)])}<br>
            <h4>max weight: </h4><br>
            {np.max(self.connectivity.weights)}<br><br></div>"""

    def display(self):
        display(self.options)
        display(self.hbox)
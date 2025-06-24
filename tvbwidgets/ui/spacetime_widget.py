# -*- coding: utf-8 -*-
#
# "TheVirtualBrain - Widgets" package
#
# (c) 2022-2025, TVB Widgets Team
#
"""
..moduleauthor:: Priya Yadav <priyayadav012004@gmail.com>
..moduleauthor:: Paula Prodan <paula.prodan@codemart.ro>
"""

import k3d
import numpy
from IPython.core.display_functions import display
from ipywidgets import HBox, BoundedFloatText, Layout, Text, Tab, HTML, Output
from matplotlib import pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.gridspec import GridSpec

from tvbwidgets.ui.base_widget import TVBWidget


class SpaceTimeVisualizerWidget(TVBWidget):

    def __init__(self, connectivity, width=900, height=600, **kwargs):
        super().__init__(**kwargs)
        self.connectivity = connectivity
        self.width = width
        self.height = height

        self._add_options()
        self.conduction_speed = self.options.children[0].value
        self.from_time = self.options.children[1].value
        self.to_time = self.options.children[2].value
        self.num_slices = 6
        self.picked_slice_id = None

        self._prepare_widget()

    def _prepare_widget(self):
        self.hbox = HBox(layout=self.DEFAULT_BORDER)
        self.tab = Tab(layout=self.DEFAULT_BORDER)

        self.plot = self._prepare_plot()
        self._prepare_scene()

        self.interactive_plot = Output(layout=Layout(width=str(self.width) + 'px', height=str(self.height) + 'px'))
        with self.interactive_plot:
            self.plot.display()

        self.plot_overview = Output()
        self._create_plots_overview()
        with self.plot_overview:
            display(self.fig)

        self.tab.children = [self.interactive_plot, self.plot_overview]
        self.tab.set_title(0, "Interactive Viewer")
        self.tab.set_title(1, "Plots Overview")

        self._prepare_plot_details()
        self.hbox.children = [self.tab, self.plot_details]

    def _get_intervals(self):
        intervals = numpy.linspace(self.from_time, self.to_time, self.num_slices + 1)
        return intervals

    def _prepare_connectivity(self, slice_id):
        """Prepares data for different slices."""
        intervals = self._get_intervals()
        if slice_id == 0:
            slice_range = self.to_time
            prev_slice_range = self.from_time
        else:
            slice_range = intervals[slice_id]
            prev_slice_range = intervals[slice_id - 1]
        time_delay = self.connectivity.tract_lengths / self.conduction_speed
        mask = (time_delay <= slice_range) & (time_delay >= prev_slice_range)
        connectivity = numpy.where(mask, self.connectivity.weights, 0)
        return connectivity

    def _get_x_translation(self, slice_id):
        if slice_id == 0:
            return - 1 / 5
        return slice_id / 5

    def _get_z_translation(self, slice_id):
        if slice_id == 0:
            return - 1 / 3
        return slice_id / 10

    def _get_transform_matrix(self, slice_id=0):
        translate = numpy.array([
            [1, 0, 0, 0 + self._get_x_translation(slice_id)],
            [0, -1, 0, 0],
            [0, 0, 1, 0 + self._get_z_translation(slice_id)],
            [0, 0, 0, 1]
        ], dtype=numpy.float32)

        return translate

    def _get_texture(self, connectivity_slice, slice_id):
        texture = k3d.texture(attribute=connectivity_slice,
                              color_map=self._custom_colormap(None),
                              color_range=[connectivity_slice.min(), connectivity_slice.max()],
                              name='Slice',
                              interpolation=False,
                              model_matrix=self._get_transform_matrix(slice_id))
        return texture

    def _change_camera_position(self, slice_id=None):
        if slice_id is None:
            # All slices view
            self.plot.camera = [-2.5, 0, 1.5,  # camera position
                                0, 0, 0,  # look at center of grid
                                0, 1, 0]
        else:
            # Single slice view
            self.plot.camera = [0 + self._get_x_translation(slice_id), 0, 2 + self._get_z_translation(slice_id),
                                0 + self._get_x_translation(slice_id), 0, 0,
                                0, 1, 0]

    def _switch_scene(self, params):
        clicked_id = params.get('K3DIdentifier')
        if self.picked_slice_id != clicked_id:
            for i in range(len(self.plot.objects)):
                texture = self.plot.objects[i]
                if texture.id != clicked_id:
                    texture.visible = False
                else:
                    self._change_camera_position(i)
                    intervals = self._get_intervals()
                    if i == 0:
                        self.selection.value = f"{intervals[0]:.2f} .. {intervals[-1]:.2f}"
                    else:
                        self.selection.value = f"{intervals[i - 1]:.2f} .. {intervals[i]:.2f}"
            self.picked_slice_id = clicked_id
        else:
            self.picked_slice_id = None
            self._change_camera_position()
            for texture in self.plot.objects:
                texture.visible = True
            self.selection.value = "None"

    def _prepare_plot(self):
        plot = k3d.Plot(grid_visible=False, camera_auto_fit=False, camera_no_rotate=True, camera_no_zoom=True,
                        camera_no_pan=True, camera_fov=30, menu_visibility=False, background_color=0x999999)
        return plot

    def _prepare_scene(self):
        for i in range(self.num_slices + 1):
            connectivity_slice = self._prepare_connectivity(i)
            texture = self._get_texture(connectivity_slice, i)
            texture.click_callback = self._switch_scene
            self.plot += texture

        self._change_camera_position()

    def display(self):
        display(self.options)
        display(self.hbox)
        self.plot.mode = 'callback'

    def _add_options(self):
        self.options = HBox(layout=self.DEFAULT_BORDER)
        max_time = self.connectivity.tract_lengths.max()
        min_time = self.connectivity.tract_lengths.min()
        self.option_conduction_speed = BoundedFloatText(
            value=1.0,
            min=0.1,
            max=round(max_time, 2),
            step=0.1,
            layout=Layout(width='170px'),
            style={'description_width': 'initial'},
            description='Conduction Speed:',
            disabled=False
        )
        self.option_conduction_speed.observe(self.on_change, names="value")

        self.option_from_time = BoundedFloatText(
            value=min_time,
            min=min_time,
            max=max_time,
            step=0.1,
            layout=Layout(width='160px'),
            description='From[ms]:',
            disabled=False
        )
        self.option_from_time.observe(self.on_change, names="value")

        self.option_to_time = BoundedFloatText(
            value=max_time,
            min=min_time,
            max=max_time,
            step=0.1,
            layout=Layout(width='160px'),
            description='To[ms]:',
            disabled=False
        )
        self.option_to_time.observe(self.on_change, names="value")

        self.selection = Text(
            value="None",
            description="Selection[ms]:",
            style={'description_width': '150px'},
            layout=Layout(width="350px"),
            disabled=True
        )
        self.options.children = [self.option_conduction_speed, self.option_from_time, self.option_to_time,
                                 self.selection]

    def on_change(self, change):
        self.plot_overview.clear_output()
        self.conduction_speed = self.options.children[0].value
        if change["owner"].description == "Conduction Speed:":
            self.options.children[1].max = self.connectivity.tract_lengths.max() / self.conduction_speed
            self.options.children[2].max = self.connectivity.tract_lengths.max() / self.conduction_speed
            self.options.children[1].min = self.connectivity.tract_lengths.min() / self.conduction_speed
            self.options.children[2].min = self.connectivity.tract_lengths.min() / self.conduction_speed
            self.options.children[1].value = self.options.children[1].min
            self.options.children[2].value = self.options.children[2].max
        self.from_time = self.options.children[1].value
        self.to_time = self.options.children[2].value
        self.plot_details.value = self._generate_details()

        for idx in range(len(self.plot.objects)):
            conn_slice = self._prepare_connectivity(idx)
            texture = self.plot.objects[idx]
            texture.attribute = conn_slice
            texture.color_range = [conn_slice.min(), conn_slice.max()]
            self.ims[idx].imshow(self._custom_colormap(conn_slice))

        with self.plot_overview:
            display(self.fig)

    def _custom_colormap(self, connectivity):
        colors = [
            '#000033', '#4d1c34', '#7a3282', '#8ea674', '#27913c', '#1c464a',
            '#247663', '#38bcaa', '#a9e9ff', '#5fcdfc', '#36a0c1', '#f99e2c',
            '#fc5326', '#df0537'
        ]
        color_scheme = mcolors.LinearSegmentedColormap.from_list('color_scheme', colors)

        if connectivity is None:
            k3d_scheme = []
            for x in numpy.linspace(0, 1, max(color_scheme.N, 256)):
                r, g, b = color_scheme(x)[:3]
                k3d_scheme.append((x, r, g, b))
            return k3d_scheme


        norm = mcolors.Normalize(vmin=0, vmax=3)
        color_data = color_scheme(norm(connectivity))[:, :, :3]
        return color_data

    def _create_plots_overview(self):
        self.fig = plt.figure(figsize=(self.width / 75.65, self.height / 75.65))
        self.ims = []
        gs = GridSpec(3, 4, figure=self.fig)
        n = self.connectivity.weights.shape[0]

        for i in range(self.num_slices + 1):
            position = gs[int(i / 3), int(i % 3)]
            ax = self.fig.add_subplot(position)
            connectivity = self._prepare_connectivity(i)
            colors = self._custom_colormap(connectivity)
            ax.imshow(colors)
            ax.set_xticks(numpy.arange(0, n, 5))
            ax.set_yticks(numpy.arange(0, n, 5))
            ax.tick_params(axis="both", labelsize=6)
            self.ims.append(ax)

        self.fig.subplots_adjust(left=0, right=1, top=1, bottom=0, wspace=0.1, hspace=0.1)
        plt.close(self.fig)

    def _prepare_plot_details(self):
        layout = self.DEFAULT_BORDER
        layout['min_width'] = "150px"
        self.plot_details = HTML(
            value=self._generate_details(),
            layout=layout
        )

    def _generate_details(self):
        return f"""<br>
            <div style="line-height:1px;">
            <br><h3>PLOT DETAILS</h3> <br><br>
            <h4>conduction speed:</h4><br> 
            {self.conduction_speed} mm/ms<br>
            <h4>min(non-zero) </h4><h4>delay: </h4><br>
            {numpy.min(self.connectivity.tract_lengths[numpy.nonzero(self.connectivity.tract_lengths)]) / self.conduction_speed} ms<br>
            <h4>max delay: </h4><br>
            {numpy.max(self.connectivity.tract_lengths) / self.conduction_speed} ms<br>
            <h4>min(non-zero) </h4><h4>tract length:</h4> <br>
            {numpy.min(self.connectivity.tract_lengths[numpy.nonzero(self.connectivity.tract_lengths)])} mm<br>
            <h4>max tract length: </h4><br>
            {numpy.max(self.connectivity.tract_lengths, )} mm<br>
            <h4>min(non-zero) </h4><h4>weight: </h4><br>
            {numpy.min(self.connectivity.weights[numpy.nonzero(self.connectivity.weights)])}<br>
            <h4>max weight: </h4><br>
            {numpy.max(self.connectivity.weights)}<br><br></div>"""

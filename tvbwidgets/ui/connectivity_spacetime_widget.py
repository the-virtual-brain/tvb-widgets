# -*- coding: utf-8 -*-
#
# "TheVirtualBrain - Widgets" package
#
# (c) 2022-2025, TVB Widgets Team
#
import k3d
import numpy
from IPython.core.display_functions import display
from ipywidgets import HBox, BoundedFloatText, Layout, Text

from tvbwidgets.ui.base_widget import TVBWidget


class ConnectivitySpaceTimeWidget(TVBWidget):

    def __init__(self, connectivity, **kwargs):
        super().__init__(**kwargs)
        self.connectivity = connectivity

        self._add_options()
        self.conduction_speed = self.options.children[0].value
        self.from_time = self.options.children[1].value
        self.to_time = self.options.children[2].value
        self.num_slices = 6
        self.picked_slice_id = None

        self.plot = self._prepare_plot()
        self._prepare_scene()

    def _prepare_connectivity(self, slice_id):
        """Prepares data for different slices."""
        intervals = numpy.linspace(self.from_time, self.to_time, self.num_slices + 1)
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

    def _get_transform_matrix(self, slice_id=0):
        # TODO: check if we need all of these
        theta = numpy.pi / 2  # 90 degrees in radians
        cos_t = numpy.cos(theta)
        sin_t = numpy.sin(theta)

        rotation_90_z = numpy.array([
            [1, 0, 0, 0],
            [0, 1, 0, 0 + slice_id / 5],
            [0, 0, 1, 0 + slice_id / 5],
            [0, 0, 0, 1]
        ], dtype=numpy.float32)

        return rotation_90_z

    def _get_texture(self, connectivity_slice, slice_id):
        # TODO: choose colormap and background color
        texture = k3d.texture(attribute=connectivity_slice,
                              color_map=k3d.basic_color_maps.WarmCool,
                              color_range=[connectivity_slice.min(), connectivity_slice.max()],
                              opacity_function=[-1, 1, 1, 1],
                              name='Slice',
                              interpolation=False,
                              model_matrix=self._get_transform_matrix(slice_id))
        return texture

    def _change_camera_position(self, single_slice=False):
        if single_slice:
            #TODO: in single slice mode camera seems backwards
            self.plot.camera = [0, -0.1, 2.3,
                                0, 0, 0,
                                -1, 0, 0]
        else:
            self.plot.camera = [0, -2, 1.2,
                                0, 0, 0,
                                -1, 0, 0]

    def _switch_scene(self, params):
        clicked_id = params.get('K3DIdentifier')
        if self.picked_slice_id != clicked_id:
            for texture in self.plot.objects:
                if texture.id != clicked_id:
                    texture.visible = False
            self._change_camera_position(True)
            self.picked_slice_id = clicked_id
        else:
            self.picked_slice_id = None
            for texture in self.plot.objects:
                texture.visible = True
            self._change_camera_position()

    def _prepare_plot(self):
        plot = k3d.Plot(grid_visible=False, camera_auto_fit=False, camera_no_rotate=True, camera_no_zoom=True,
                        camera_no_pan=True, camera_fov=30, menu_visibility=True, background_color=0x999999)
        return plot

    def _prepare_scene(self):

        for i in range(self.num_slices + 1):
            connectivity_slice = self._prepare_connectivity(i)
            texture = self._get_texture(connectivity_slice, i)
            texture.click_callback = self._switch_scene
            self.plot += texture

        self._change_camera_position()

        # group = k3d.objects.Group([texture, texture1, texture2, texture3])
        # plot += group

    def display(self):
        display(self.options)
        self.plot.display()
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
            description='from[ms]:',
            disabled=False
        )
        self.option_from_time.observe(self.on_change, names="value")

        self.option_to_time = BoundedFloatText(
            value=max_time,
            min=min_time,
            max=max_time,
            step=0.1,
            layout=Layout(width='160px'),
            description='to[ms]:',
            disabled=False
        )
        self.option_to_time.observe(self.on_change, names="value")

        self.selection = Text(
            value="None",
            description="selection[ms]:",
            layout=Layout(width="200px")
        )
        self.options.children = [self.option_conduction_speed, self.option_from_time, self.option_to_time,
                                 self.selection]

    def on_change(self, change):
        # self.graphs_matplotlib.clear_output()
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
        # self.plot_details.value = self._generate_details()

        self.plot.auto_rendering = False
        while self.plot.objects:
            self.plot -= self.plot.objects[-1]

        self.plot.auto_rendering = True
        self._prepare_scene()
        #     self.ims[i].imshow(data)
        #
        # with self.graphs_matplotlib:
        #     display(self.fig)
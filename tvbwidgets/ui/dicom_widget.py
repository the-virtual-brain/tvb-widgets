# -*- coding: utf-8 -*-
#
# "TheVirtualBrain - Widgets" package
#
# (c) 2022-2025, TVB Widgets Team
#
from enum import Enum

import numpy as np
from bokeh.events import Tap
from bokeh.io import show
from bokeh.layouts import row, column
from bokeh.models import Slider, CrosshairTool
from bokeh.palettes import Greys256
from bokeh.plotting import figure
from tvb.datatypes.structural import StructuralMRI

from tvbwidgets.ui.base_widget import TVBWidget


class PlotType(Enum):
    AXIAL = 'axial'
    SAGITTAL = 'sagittal'
    CORONAL = 'coronal'


class DicomPlot:
    def __init__(self, data=None, title='Plot View', name='Plot', plot_type=None, xrange=None, yrange=None, height=250,
                 width=250, color_palette=Greys256, dw=0, dh=0, x_index=0, y_index=0):
        # Data
        self.data = data
        self.plot_type = plot_type
        self.x_index = x_index
        self.y_index = y_index

        # Plot design
        self.title = title
        self.name = name
        self.xrange = xrange
        self.yrange = yrange
        self.height = height
        self.width = width
        self.color_palette = color_palette
        self.dw = dw
        self.dh = dh

        # Bokeh plotting
        self.figure = figure(
            title=self.title,
            x_range=self.xrange,
            y_range=self.yrange,
            name=self.name,
            height=self.height,
            width=self.width
        )
        # Edit plot tools
        self.figure.toolbar.active_drag = None  # Deactivate pan tool so users don't mistakenly move the plot
        crosshair = CrosshairTool(dimensions='both', line_color='orangered', line_width=2)
        self.figure.add_tools(crosshair)

        # Add data to plot
        self.image = self.figure.image(
            image=[self.data],
            x=0,
            y=0,
            dw=self.dw,
            dh=self.dh,
            palette=self.color_palette
        )

        # Add crosshair glyph
        self.figure.scatter(marker='cross', x=self.x_index, y=self.y_index, size=40, line_width=3, alpha=1,
                            color='lawngreen')

    def update_on_tap(self, event, slider1, slider2):
        # Update indices based on the tapped location
        x_index, y_index = int(event.x), int(event.y)

        # Update corresponding sliders
        y_index = self.figure.y_range.end - y_index
        slider1.value = x_index
        slider2.value = y_index


class DicomWidget(TVBWidget):
    def __init__(self, data=None, **kwargs):
        super().__init__()
        # Data
        self.data = None
        self.add_datatype(data)
        # Indices for data on all 3 axes - display initially the middle of each view
        self.x_index = data.shape[0] // 2
        self.y_index = data.shape[1] // 2
        self.z_index = data.shape[2] // 2

        # Plots
        self.main_plot_name = PlotType.AXIAL  # used to keep track of which plot is displayed in main view
        self.axial_plot = DicomPlot(data=self.data[:, :, self.z_index],
                                    title='Axial Plot', name='Axial View', plot_type=PlotType.AXIAL,
                                    xrange=(0, self.data.shape[2] - 1), yrange=(0, self.data.shape[1] - 1),
                                    dw=self.data.shape[1], dh=self.data.shape[0],
                                    x_index=self.y_index, y_index=self.x_index
                                    )
        self.sagittal_plot = DicomPlot(data=self.data[self.x_index, :, :].T,
                                       title='Sagittal Plot', name='Sagittal View', plot_type=PlotType.SAGITTAL,
                                       xrange=(0, self.data.shape[2] - 1), yrange=(0, self.data.shape[0] - 1),
                                       dw=self.data.shape[2], dh=self.data.shape[1],
                                       x_index=self.y_index, y_index=self.z_index)
        self.coronal_plot = DicomPlot(data=self.data[:, self.y_index, :].T,
                                      title='Coronal Plot', name='Coronal View', plot_type=PlotType.CORONAL,
                                      xrange=(0, self.data.shape[1] - 1), yrange=(0, self.data.shape[0] - 1),
                                      dw=self.data.shape[2], dh=self.data.shape[1],
                                      x_index=self.x_index, y_index=self.z_index)
        self.main_plot = DicomPlot(data=None,
                                   title='Main Plot', name='Main View',
                                   xrange=(0, self.data.shape[2] - 1), yrange=(0, self.data.shape[1] - 1),
                                   height=750, width=750
                                   )
        self.main_plot.figure.renderers = self.axial_plot.figure.renderers

        # Sliders
        self.x_slider = Slider(start=0, end=self.data.shape[0] - 1, value=self.x_index, step=1, title="X Axis")
        self.y_slider = Slider(start=0, end=self.data.shape[1] - 1, value=self.y_index, step=1, title="Y Axis")
        self.z_slider = Slider(start=0, end=self.data.shape[2] - 1, value=self.z_index, step=1, title="Z Axis")

        self.x_slider.on_change('value', self.update_x)
        self.y_slider.on_change('value', self.update_y)
        self.z_slider.on_change('value', self.update_z)

        # Add callbacks for Tap events
        self.axial_plot.figure.on_event(Tap, self.handle_tap_axial)
        self.sagittal_plot.figure.on_event(Tap, self.handle_tap_sagittal)
        self.coronal_plot.figure.on_event(Tap, self.handle_tap_coronal)
        self.main_plot.figure.on_event(Tap, self.handle_tap_main)

        # Final layout
        self.layout = column(
            row(self.x_slider, self.y_slider, self.z_slider),
            row(
                column(self.axial_plot.figure, self.sagittal_plot.figure, self.coronal_plot.figure),
                self.main_plot.figure
            )
        )

    def add_datatype(self, datatype):  # type: (HasTraits) -> None
        if datatype is None:
            raise ValueError('The provided datatype is None!')
        if isinstance(datatype, StructuralMRI):
            data = datatype.array_data
        elif isinstance(datatype, np.ndarray):
            data = datatype
        else:
            raise ValueError(f'Datatype {type(datatype)} not supported by this widget!')

        # Validate data
        if data.ndim != 3:
            raise ValueError(f'Expected input data with 3 dimensions, but got {data.ndim} instead!')
        x_dim, y_dim, z_dim = data.shape
        if not (x_dim == y_dim == z_dim):
            raise ValueError(f'Expected input data with the same number of elements on all 3 axes, '
                             f'but instead got X axis with {x_dim} elements, Y axis with {y_dim} elements '
                             f'and Z axis with {z_dim} elements!')

        # Set data on widget
        self.data = data

    # =========================================== UPDATE SLIDERS =======================================================
    def update_x(self, attr, old, new):
        # Update corresponding plot
        self.sagittal_plot.image.data_source.data['image'] = [self.data[new, :, :].T]

        # Update corresponding crosshairs
        self.update_crosshair_glyph(plot=self.axial_plot, y_coord=255 - new)
        self.update_crosshair_glyph(plot=self.coronal_plot, x_coord=new)

    def update_y(self, attr, old, new):
        # Update corresponding plot
        self.coronal_plot.image.data_source.data['image'] = [self.data[:, new, :].T]

        # Update corresponding crosshairs
        self.update_crosshair_glyph(plot=self.axial_plot, x_coord=new)
        self.update_crosshair_glyph(plot=self.sagittal_plot, x_coord=new)

    def update_z(self, attr, old, new):
        self.axial_plot.image.data_source.data['image'] = [self.data[:, :, 255 - new]]

        # Update corresponding crosshairs
        self.update_crosshair_glyph(plot=self.sagittal_plot, y_coord=255 - new)
        self.update_crosshair_glyph(plot=self.coronal_plot, y_coord=255 - new)

    # ===================================== UPDATE PLOTS ON TAP EVENT ==================================================
    def handle_tap_axial(self, event):
        # Set main plot to be the axial one
        self.main_plot.figure.renderers = self.axial_plot.figure.renderers
        self.main_plot_name = PlotType.AXIAL
        self.axial_plot.update_on_tap(event=event, slider1=self.y_slider, slider2=self.x_slider)

    def handle_tap_sagittal(self, event):
        # Set main plot to be the sagittal one
        self.main_plot.figure.renderers = self.sagittal_plot.figure.renderers
        self.main_plot_name = PlotType.SAGITTAL
        self.sagittal_plot.update_on_tap(event=event, slider1=self.y_slider, slider2=self.z_slider)

    def handle_tap_coronal(self, event):
        # Set main plot to be the coronal one
        self.main_plot.figure.renderers = self.coronal_plot.figure.renderers
        self.main_plot_name = PlotType.CORONAL
        self.coronal_plot.update_on_tap(event=event, slider1=self.x_slider, slider2=self.z_slider)

    def handle_tap_main(self, event):
        if self.main_plot_name == PlotType.AXIAL:
            self.main_plot.update_on_tap(event=event, slider1=self.y_slider, slider2=self.x_slider)
        if self.main_plot_name == PlotType.SAGITTAL:
            self.main_plot.update_on_tap(event=event, slider1=self.y_slider, slider2=self.z_slider)
        if self.main_plot_name == PlotType.CORONAL:
            self.main_plot.update_on_tap(event=event, slider1=self.x_slider, slider2=self.z_slider)

    # ========================================== UPDATE CROSSHAIR ======================================================
    @staticmethod
    def update_crosshair_glyph(plot, x_coord=None, y_coord=None):
        """
        :param: plot - DicomPlot object on which a touch event happened
        :param: x_coord - X axis coordinate where touch event happened
        :param: y_coord - Y axis coordinate where touch event happened
        """
        if x_coord:
            plot.figure.renderers[1].glyph.x = x_coord
        if y_coord:
            plot.figure.renderers[1].glyph.y = y_coord

    # =========================================== DISPLAY WIDGET =======================================================
    def embed_layout(self, doc):
        doc.add_root(self.layout)

    def show_widget(self):
        show(self.embed_layout)

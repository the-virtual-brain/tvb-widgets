# -*- coding: utf-8 -*-
#
# "TheVirtualBrain - Widgets" package
#
# (c) 2022-2025, TVB Widgets Team
#

import numpy as np
import ipywidgets as widgets
import matplotlib.pyplot as plt
import matplotlib.colors as mlt
from IPython.core.display_functions import display
from plotly_resampler import register_plotly_resampler, FigureWidgetResampler
from tvbwidgets.ui.ts.base_ts_widget import TimeSeriesWidgetBase


class TimeSeriesWidgetPlotly(TimeSeriesWidgetBase):
    """ TimeSeries Widget drawn using plotly"""

    def __init__(self, **kwargs):
        # data
        self.fig = None
        self.data = None
        self.ch_names = []
        self.ch_picked = []
        self.raw = None
        self.sample_freq = 0
        self.start_time = 0
        self.end_time = 0
        self.std_step = 0
        self.amplitude = 1
        self.colormap = None

        # plot & UI
        self.checkboxes = dict()
        self.plot_area = widgets.HBox()
        self.output = widgets.Output()
        self.channel_selection_area = widgets.HBox(layout=widgets.Layout(width='90%'))
        self.info_and_channels_area = widgets.HBox(layout=widgets.Layout(margin='0px 0px 0px 80px'))
        self.plot_area.children += (self.output,)
        self.scaling_title = widgets.Label(
            value='Increase/Decrease signal scaling (current scaling value to the right)')
        self.scaling_slider = widgets.IntSlider(value=1, layout=widgets.Layout(width='30%'))
        self.colormaps = ['turbo', 'brg', 'gist_stern_r', 'nipy_spectral_r', 'coolwarm', 'plasma', 'magma', 'viridis', \
                          'cividis', 'twilight', 'twilight_shifted', 'CMRmap_r', 'Blues', \
                          'BuGn', 'BuPu', 'Greens', 'PuRd', 'RdPu', 'Spectral', 'YlGnBu', \
                          'YlOrBr', 'YlOrRd', 'cubehelix_r', 'gist_earth_r', 'terrain_r', \
                          'rainbow_r', 'pink_r', 'gist_ncar_r', 'uni-color(black)']
        self.colormap_dropdown = widgets.Dropdown(options=self.colormaps, description='Colormap:', disabled=False)
        self.colormap_dropdown.observe(self.update_colormap, names='value')

        super().__init__(
            [self.plot_area, widgets.VBox([self.colormap_dropdown, self.scaling_title, self.scaling_slider],
                                          layout=widgets.Layout(margin='0px 0px 0px 80px')),
             self.info_and_channels_area],
            layout=self.DEFAULT_BORDER)
        self.logger.info("TimeSeries Widget with Plotly initialized")

    # =========================================== SETUP ================================================================
    def _populate_from_data_wrapper(self, data_wrapper):
        super()._populate_from_data_wrapper(data_wrapper=data_wrapper)
        self.ch_picked = list(range(len(self.ch_names)))
        del self.ch_order, self.ch_types  # delete these as we don't use them in plotly
        # populate channel selection area
        self.channels_area = self._create_channel_selection_area(array_wrapper=data_wrapper)
        self._setup_scaling_slider()
        self.channel_selection_area.children += (self.channels_area,)
        # populate info area
        info = self._create_info_area()
        self.info_and_channels_area.children += (info, self.channel_selection_area)
        self.plot_ts_with_plotly()

    # =========================================== PLOT =================================================================
    def add_traces_to_plot(self, data, ch_names):
        """ Draw the traces """
        # traces will be added from bottom to top, so reverse the lists to put the first channel on top
        data = data[::-1]
        ch_names = ch_names[::-1]
        if self.colormap == "uni-color(black)":
            colormap = plt.get_cmap('gray')
            colors = colormap(np.linspace(0, 0, len(ch_names)))
        else:
            colormap = plt.get_cmap(self.colormap)
            colors = colormap(np.linspace(0.3, 1, len(ch_names)))
        colors = [mlt.to_hex(color, keep_alpha=False) for color in colors]

        self.fig.add_traces(
            [dict(y=ts * self.amplitude + i * self.std_step, name=ch_name, customdata=ts, hovertemplate='%{customdata}',
                  line_color=colors[i])
             for i, (ch_name, ts) in enumerate(zip(ch_names, data))]
        )

    def _populate_plot(self, data=None, ch_names=None):
        # create traces for each signal
        data_from_raw = self.raw[:, :][0]
        data = data if data is not None else data_from_raw
        ch_names = ch_names if ch_names is not None else self.ch_names
        self.std_step = 10 * np.max(np.std(data, axis=1))

        self.add_traces_to_plot(data, ch_names)

        # display channel names for each trace
        for i, ch_name in enumerate(ch_names[::-1]):
            self.fig.add_annotation(
                x=0.0, y=i * self.std_step,
                text=ch_name,
                showarrow=False,
                xref='paper',
                xshift=-70
            )

        # add ticks between channel names and their traces
        self.fig.update_yaxes(fixedrange=False, showticklabels=False, ticks='outside', ticklen=3,
                              tickvals=np.arange(len(ch_names)) * self.std_step)

        # configure legend
        self.fig.update_layout(
            # traces are added from bottom to top, but legend displays the names from top to bottom
            legend={'traceorder': 'reversed'}
        )

    def add_visibility_buttons(self):
        # buttons to show/hide all traces
        self.fig.update_layout(dict(updatemenus=[dict(type="buttons", direction="left",
                                                      buttons=list([dict(args=["visible", True], label="Show All",
                                                                         method="restyle"),
                                                                    dict(args=["visible", 'legendonly'],
                                                                         label="Hide All",
                                                                         method="restyle")
                                                                    ]),
                                                      showactive=False,  # personal preference
                                                      # position buttons in bottom left corner of plot
                                                      x=0,
                                                      xanchor="left",
                                                      y=-0.1,
                                                      yanchor="bottom")]
                                    ))

    def create_plot(self, data=None, ch_names=None):
        # register resampler so every plot will benefit from it
        register_plotly_resampler(mode='auto')

        self.fig = FigureWidgetResampler()

        self._populate_plot(data, ch_names)

        # different visual settings
        self.fig.update_layout(
            width=1000, height=800,
            showlegend=True,
            template='plotly_white'
        )

        self.add_visibility_buttons()

    def plot_ts_with_plotly(self, data=None, ch_names=None):
        self.create_plot(data, ch_names)
        with self.output:
            self.output.clear_output(wait=True)
            display(self.fig)

    def update_colormap(self, change):
        self.colormap = change['new']
        self.fig.data = []
        data = self.raw[:, :][0]
        data = data[self.ch_picked, :]
        ch_names = [self.ch_names[i] for i in self.ch_picked]
        self.add_traces_to_plot(data, ch_names)

    # ================================================= SCALING ========================================================
    def _setup_scaling_slider(self):
        # set min and max scaling values
        self.scaling_slider.min = 1
        self.scaling_slider.max = 10
        self.scaling_slider.observe(self.update_scaling, names='value', type='change')

    def update_scaling(self, val):
        """ Update the amplitude of traces based on slider value """
        new_val = val['new']
        self.amplitude = new_val

        # delete old traces
        self.fig.data = []
        data = self.raw[:, :][0]
        data = data[self.ch_picked, :]
        ch_names = [self.ch_names[i] for i in self.ch_picked]
        self.add_traces_to_plot(data, ch_names)

    # =========================================== CHANNELS SELECTION ===================================================
    def _create_channel_selection_area(self, array_wrapper, no_checkbox_columns=5):
        # type: (ABCDataWrapper) -> widgets.Accordion
        """ Create the whole channel selection area: Submit button to update plot, Select/Uselect all buttons,
            State var. & Mode selection and Channel checkboxes
        """
        # checkboxes
        checkboxes_region = self._create_checkboxes(array_wrapper=array_wrapper,
                                                    no_checkbox_columns=no_checkbox_columns)
        for cb_stack in checkboxes_region.children:
            cb_stack.layout = widgets.Layout(width='100%')

        # selection submit button
        self.submit_selection_btn = widgets.Button(description='Submit selection', layout=self.BUTTON_STYLE,
                                                   button_style="info")
        self.submit_selection_btn.on_click(self._update_ts)

        # select/unselect all buttons
        select_all_btn, unselect_all_btn = self._create_select_unselect_all_buttons()

        # select dimensions buttons (state var. & mode)
        selections = self._create_dim_selection_buttons(array_wrapper=array_wrapper)
        for selection in selections:
            selection.layout = widgets.Layout(width='50%')

        # add all buttons to channel selection area
        channels_region = widgets.VBox(children=[widgets.HBox([self.submit_selection_btn,
                                                               select_all_btn, unselect_all_btn]),
                                                 widgets.HBox(selections),
                                                 checkboxes_region])
        channels_area = widgets.Accordion(children=[channels_region], selected_index=None,
                                          layout=widgets.Layout(width='70%'))
        channels_area.set_title(0, 'Channels')
        return channels_area

    def _update_ts(self, btn):
        self.logger.debug('Updating TS')
        ch_names = list(self.ch_names)

        # save selected channels using their index in the ch_names list
        self.ch_picked = []
        for cb in list(self.checkboxes.values()):
            ch_index = ch_names.index(cb.description)  # get the channel index
            if cb.value:
                self.ch_picked.append(ch_index)  # list with number representation of channels

        # if unselect all
        # TODO: should we remove just the traces and leave the channel names and the ticks??
        if not self.ch_picked:
            self.fig.data = []  # remove traces
            self.fig.layout.annotations = []  # remove channel names
            self.fig.layout.yaxis.tickvals = []  # remove ticks between channel names and traces
            return

        # get data and names for selected channels; self.raw is updated before redrawing starts
        data, _ = self.raw[:, :]
        data = data[self.ch_picked, :]
        ch_names = [ch_names[i] for i in self.ch_picked]

        # redraw the entire plot
        self.plot_ts_with_plotly(data, ch_names)

    # ================================================ INFO AREA =======================================================
    def _create_info_area(self):
        # navigate through timeline
        navigate_timeline_title = widgets.HTML(value='<b>Navigate timeline</b>')
        navigate_timeline_text = 'To navigate through the timeline, go with your cursor over the timeline (bottom ' \
                                 'area of the plot). When you see the \'↔\' symbol, click and drag your ' \
                                 'cursor to the left/right to navigate through the timeline.'
        navigate_timeline_label = widgets.HTML(value=navigate_timeline_text)

        # modify spacing between channels
        modify_spacing_title = widgets.HTML(value='<b>Modify spacing</b>')

        modify_spacing_text = 'To increase the spacing between the channels, go with your cursor over the' \
                              ' very bottom or very top part of the y-axis. When you see the \'↕\' symbol, ' \
                              'click and drag your cursor outside the plot area to increase the spacing between ' \
                              'the channels. ' \
                              'To decrease the spacing, click and drag towards the plot area.'
        modify_spacing_label = widgets.HTML(value=f'{modify_spacing_text}')

        # modify signal amplitude
        modify_amplitude_title = widgets.HTML(value='<b>Modify signal amplitude</b>')
        modify_amplitude_text = 'To modify the amplitude of the signals, use the above slider. Dragging to the' \
                                'right means increasing the amplitude, dragging to the left means decreasing it. ' \
                                'The value by which the signals are multiplied is written to the right.'
        modify_amplitude_label = widgets.HTML(value=f'{modify_amplitude_text}')

        # additional info and link to wiki
        additional_info_title = widgets.HTML(value='<b>Additional information</b>')
        additional_info_text = 'For more information about this widget and and example videos on how to use it, ' \
                               'visit: '
        additional_info_label = widgets.HTML(value=f"{additional_info_text} "
                                                   f"<a href=https://wiki.ebrains.eu/bin/view/Collabs/tvb-widgets/Widget%20TimeSeries/ target='_blank'>"
                                                   f"https://wiki.ebrains.eu/bin/view/Collabs/tvb-widgets/Widget%20TimeSeries/"
                                                   f"</a>")

        more_info_container = widgets.VBox(children=[navigate_timeline_title, navigate_timeline_label,
                                                     modify_spacing_title, modify_spacing_label, modify_amplitude_title,
                                                     modify_amplitude_label, additional_info_title,
                                                     additional_info_label],
                                           layout=widgets.Layout(height='370px'))
        info_area = widgets.Accordion(children=[more_info_container], selected_index=None,
                                      layout=widgets.Layout(width='50%'))
        info_area.set_title(0, 'More info')
        return info_area

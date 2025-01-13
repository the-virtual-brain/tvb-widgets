# -*- coding: utf-8 -*-
#
# "TheVirtualBrain - Widgets" package
#
# (c) 2022-2025, TVB Widgets Team
#

import colorsys
import ipywidgets as widgets
import matplotlib.pyplot as plt
import numpy as np
import tvb.simulator.integrators as integrators_module
import tvb.simulator.models as models_module
from IPython.core.getipython import get_ipython
from tvb.basic.neotraits.api import HasTraits, Attr, NArray
from tvb.simulator.lab import integrators
from tvbwidgets.core.simulator.model_exporters import model_exporter_factory, ModelConfigurationExports
from tvbwidgets.core.simulator.model_exporters import PythonCodeExporter
from tvbwidgets.ui.base_widget import TVBWidget
from tvbwidgets.core.simulator.tvb_integrators import IntegratorsEnum


def get_color(num_colours):
    for hue in range(num_colours):
        hue = 1.0 * hue / num_colours
        col = [int(x) for x in colorsys.hsv_to_rgb(hue, 1.0, 230)]
        yield "#{0:02x}{1:02x}{2:02x}".format(*col)


class PhasePlaneWidget(HasTraits, TVBWidget):
    """
    The GUI for the interactive phase-plane viewer provides sliders for setting:
        - The value of all parameters of the Model.
        - The extent of the axes.
        - A fixed value for the state-variables which aren't currently selected.
        - The noise strength, if a stochastic integrator is specified.

    and dropdown lists for selecting:
        - Which state-variables to show on each axis.
        - Which mode to show, if the Model has them.

    Entering the coordinates in the X,Y Coordinate Boxes will generate a sample
    trajectory, originating from the coordinates entered.

    """
    # Set the resolution of the phase-plane and sample trajectories.
    NO_GRID_POINTS = 42
    TRAJ_STEPS = 6144

    model = Attr(
        field_type=models_module.Model,
        label="Model",
        default=models_module.Generic2dOscillator(),
        doc="""An instance of the local dynamic model to be investigated with
        PhasePlaneInteractive.""")

    integrator = Attr(
        field_type=integrators_module.Integrator,
        label="Integrator",
        default=integrators_module.RungeKutta4thOrderDeterministic(),
        doc="""The integration scheme used to for generating sample
        trajectories on the phase-plane. NOTE: This is not used for generating
        the phase-plane itself, ie the vector field and nullclines.""")

    def __init__(self, **kwargs):
        """ Initialise based on provided keywords or their traited defaults. """

        super(PhasePlaneWidget, self).__init__(**kwargs)

        self.export_filename = None
        self.disable_model_dropdown = False
        self.disable_export_dropdown = False
        self.plot_size = 4, 5
        self.plot_main_axes = None
        self.plot_bellow = None
        self.noise_sliders = []
        if hasattr(self.integrator, 'noise'):
            self.noise_slider_valinit = self.integrator.noise.nsig[0]
        else:
            self.noise_slider_valinit = 0
        self.trajectories = []
        # Parameters to be passed to plotter when their change affects the drawing
        self.params = dict()

        # Prepare the initial state
        self.svx = self.model.state_variables[0]  # x-axis: 1st state variable
        self.svy = self.model.state_variables[1]  # y-axis: 2nd state variable
        self.mode = 0

        # LAYOUTS
        self.slider_layout = widgets.Layout(width='90%')
        self.slider_style = {'description_width': 'initial'}
        self.button_layout = widgets.Layout(width='90%')
        self.other_layout = widgets.Layout(width='90%')
        self.box_layout = widgets.Layout(border='solid 1px black',
                                         margin='0px 5px 5px 0px',
                                         padding='2px 2px 2px 2px')

        # Toggle variable for trajectory
        self.traj_out = None

        # Create message area
        self.message_area = widgets.HTML(value="", layout=widgets.Layout(margin="0px 0px 0px 22px"))

    def plotter(self, **plot_params):
        """
        Main plotter function, (re)drawing the main Phase Plane canvases.
        """
        if self.plot_main_axes is None:
            self.plot_main_axes, self.plot_bellow = self._init_plot()
        else:
            self.plot_main_axes.clear()
            self.plot_bellow.clear()

        # Fetching the parameter values from tvb-widgets.
        svx = plot_params.pop('svx')
        svy = plot_params.pop('svy')
        mode = plot_params.pop('mode')

        # Set Model Parameters
        for k, v in plot_params.items():
            setattr(self.model, k, np.r_[v])

        noise_element_exists = 'noise_slider_' + str(self.model.state_variables[0])
        if noise_element_exists in plot_params:
            # Update integrator noise based on the noise slider value, for stochastic integrators
            noise_sliders = []
            for state_variable in self.model.state_variables:
                noise_sliders.append([[plot_params.pop('noise_slider_' + str(state_variable))]])
            if hasattr(self.integrator, 'noise'):
                self.integrator.noise.nsig = np.array(noise_sliders)

        # Set State Vector
        sv_mean = np.array([plot_params[key] for key in self.model.state_variables])
        sv_mean = sv_mean.reshape((self.model.nvar, 1, 1))
        default_sv = sv_mean.repeat(self.model.number_of_modes, axis=2)
        no_coupling = np.zeros((self.model.nvar, 1, self.model.number_of_modes))

        # Set Mesh Grid
        xlo = plot_params['sl_x_min']
        xhi = plot_params['sl_x_max']
        ylo = plot_params['sl_y_min']
        yhi = plot_params['sl_y_max']

        x = np.mgrid[xlo:xhi:(self.NO_GRID_POINTS * 1j)]
        y = np.mgrid[ylo:yhi:(self.NO_GRID_POINTS * 1j)]

        # Calculate Phase Plane
        svx_ind = self.model.state_variables.index(svx)
        svy_ind = self.model.state_variables.index(svy)

        # Calculate the vector field discretely sampled at a grid of points
        grid_point = default_sv.copy()
        u = np.zeros((self.NO_GRID_POINTS, self.NO_GRID_POINTS, self.model.number_of_modes))
        v = np.zeros((self.NO_GRID_POINTS, self.NO_GRID_POINTS, self.model.number_of_modes))

        for ii in range(self.NO_GRID_POINTS):
            grid_point[svy_ind] = y[ii]
            for jj in range(self.NO_GRID_POINTS):
                grid_point[svx_ind] = x[jj]
                d = self.model.dfun(grid_point, no_coupling)
                for kk in range(self.model.number_of_modes):
                    u[ii, jj, kk] = d[svx_ind, 0, kk]
                    v[ii, jj, kk] = d[svy_ind, 0, kk]

        model_name = self.model.__class__.__name__
        self.plot_main_axes.set(title=model_name + " mode " + str(mode))
        self.plot_main_axes.set(xlabel="State Variable " + svx)
        self.plot_main_axes.set(ylabel="State Variable " + svy)

        # Plot a discrete representation of the vector field
        if np.all(u[:, :, mode] + v[:, :, mode] == 0):
            self.plot_main_axes.set(title=model_name + " mode " + str(mode) + ": NO MOTION IN THIS PLANE")
            x, y = np.meshgrid(x, y)
            self.plot_main_axes.scatter(x, y, s=8, marker=".", c="k")
        else:
            self.plot_main_axes.quiver(x, y, u[:, :, mode], v[:, :, mode], width=0.001, headwidth=8)

        # Plot the nullclines
        self.plot_main_axes.contour(x, y, u[:, :, mode], [0], colors="r")
        self.plot_main_axes.contour(x, y, v[:, :, mode], [0], colors="g")

        self.plot_trajectories(svx, svy, default_sv, no_coupling, mode, self.plot_main_axes, self.plot_bellow,
                               **plot_params)
        plt.show()

    def _init_plot(self):
        try:
            ipp_fig = plt.figure(num="Phase Plane", figsize=self.plot_size)
        except ValueError:
            # In case a text can not be given instead of the figure number
            ipp_fig = plt.figure(figsize=self.plot_size)
        pp_ax = ipp_fig.add_axes([0.15, 0.2, 0.8, 0.75])
        pp_splt = ipp_fig.add_subplot(212)
        ipp_fig.subplots_adjust(left=0.15, bottom=0.04, right=0.95,
                                top=0.3, wspace=0.1, hspace=1.0)
        pp_splt.plot(np.arange(self.TRAJ_STEPS + 1) * self.integrator.dt,
                     np.zeros((self.TRAJ_STEPS + 1, self.model.nvar)))
        if hasattr(pp_splt, 'autoscale'):
            pp_splt.autoscale(enable=True, axis='y', tight=True)

        def on_click(event):
            if event.inaxes == self.plot_main_axes:
                self.traj_x.value = event.xdata
                self.traj_y.value = event.ydata
                self.plot_traj_button.click()

        ipp_fig.canvas.mpl_connect('button_press_event', on_click)
        return pp_ax, pp_splt

    def plot_trajectories(self, svx, svy, default_sv, no_coupling, mode, pp_ax, pp_splt, **plot_params):

        # Fetching Trajectory Coordinates and storing in a list.
        traj_x = plot_params.pop('traj_x')
        traj_y = plot_params.pop('traj_y')
        plot_traj = plot_params.pop('plot_traj')

        if plot_traj and (traj_x, traj_y) not in self.trajectories:
            self.trajectories.append((traj_x, traj_y))

        # Clearing Plotted Trajectories.
        clear_traj = plot_params.pop('clear_traj')
        if clear_traj:
            self.trajectories.clear()

        # Plot Trajectories
        for traj_text in self.trajectories:

            x = float(traj_text[0])
            y = float(traj_text[1])
            svx_ind = self.model.state_variables.index(svx)
            svy_ind = self.model.state_variables.index(svy)

            # Calculate an example trajectory
            state = default_sv.copy()
            self.integrator.clamped_state_variable_indices = np.setdiff1d(
                np.r_[:len(self.model.state_variables)], np.r_[svx_ind, svy_ind])
            self.integrator.clamped_state_variable_values = default_sv[
                self.integrator.clamped_state_variable_indices]
            state[svx_ind] = x
            state[svy_ind] = y
            scheme = self.integrator.scheme
            traj = np.zeros((self.TRAJ_STEPS + 1, self.model.nvar, 1, self.model.number_of_modes))
            traj[0, :] = state
            for step in range(self.TRAJ_STEPS):
                state = scheme(state, self.model.dfun, no_coupling, 0.0, 0.0)
                traj[step + 1, :] = state

            pp_ax.scatter(x, y, s=42, c='g', marker='o', edgecolor=None)
            pp_ax.plot(traj[:, svx_ind, 0, mode], traj[:, svy_ind, 0, mode])

            # Plot the selected state variable trajectories as a function of time
            pp_splt.set_prop_cycle(color=get_color(self.model.nvar))
            pp_splt.plot(np.arange(self.TRAJ_STEPS + 1) * self.integrator.dt, traj[:, :, 0, mode])
            pp_splt.legend(self.model.state_variables)

    def get_widget(self, plot_size=(4, 5)):
        """ Generate the Phase Plane Figure and Widgets. """
        self.plot_size = plot_size
        # Make sure the model is configured.
        self.model.configure()

        # Create UI with Widgets
        self.ui = self.create_ui()

        # Generate Output
        self.out = widgets.interactive_output(self.plotter, self.params)

        self.hbox = widgets.HBox([self.ui, self.out], layout=self.DEFAULT_BORDER)

        return self.hbox

    # ------------------------------------------------------------------------#
    # ----------------- Functions for populating the figure ------------------#
    # ------------------------------------------------------------------------#

    def create_ui(self):
        # Figure and main phase-plane axes
        self.set_state_vector()

        # Axes Sliders and Reset Button
        self.add_axes_sliders()
        self.add_reset_axes_button()

        # Param Sliders and Reset Button
        self.add_param_sliders()
        self.add_reset_param_button()

        # State Variable Sliders and Reset Button
        self.add_sv_sliders()
        self.add_reset_sv_button()

        # XY Axes State Variable Selector and Mode Selector
        self.add_sv_selector()
        self.add_mode_selector()

        # Widget Group "Axes"
        self.mode_selector_widget = widgets.VBox([widgets.Label('Mode Selector'), self.mode_selector])
        self.svx_widget = widgets.VBox([widgets.Label('State Var. on X axis:'), self.state_variable_x])
        self.svy_widget = widgets.VBox([widgets.Label('State Var. on Y axis:'), self.state_variable_y])
        axes_widgets_list = [self.svx_widget, self.svy_widget, self.mode_selector_widget,
                             self.sl_x_min, self.sl_x_max, self.sl_y_min, self.sl_y_max, self.reset_axes_button,
                             widgets.Label('Values for SV that are not on the axes')] + \
                            list(self.sv_sliders.values()) + [self.reset_sv_button]
        self.ax_widgets = widgets.VBox(axes_widgets_list, layout=self.box_layout)

        # Widget Group "Trajectories
        self.add_traj_coords_text()
        self.sv_widgets = widgets.VBox([self.traj_label, self.traj_x_box, self.traj_y_box,
                                        self.plot_traj_button, self.traj_out, self.clear_traj_button],
                                       layout=self.box_layout)

        # Widget Group "Model"
        self._add_model_selector()
        self._add_integrator_selector()
        widgets_integrator = self.add_integrator_widgets()
        self.param_widgets = widgets.VBox([self.model_selector] + list(self.param_sliders.values()) +
                                          [self.reset_param_button, self.integrator_selector, self.message_area] +
                                          widgets_integrator, layout=self.box_layout)

        # Exports
        self.build_export_section()

        # Group all Widgets in tabs
        return self._build_top_tabs()

    def _build_top_tabs(self):
        tab_parent = widgets.Tab()
        tab_parent.children = [self.param_widgets, self.sv_widgets, self.ax_widgets, self.export_model_section]
        tab_titles = ['Model', 'Trajectories', 'Axes', 'Exports']
        for i in range(4):
            tab_parent.set_title(i, tab_titles[i])
        return tab_parent

    def add_reset_axes_button(self):
        """ Add a button to reset the axes of the Phase Plane to their default ranges. """

        def reset_ranges(_):
            self.sl_x_min.value = self.sl_x_min_initval
            self.sl_x_max.value = self.sl_x_max_initval
            self.sl_y_min.value = self.sl_y_min_initval
            self.sl_y_max.value = self.sl_y_max_initval

        self.reset_axes_button = widgets.Button(description='Reset axes',
                                                disabled=False,
                                                layout=self.button_layout)
        self.reset_axes_button.on_click(reset_ranges)

    def add_reset_sv_button(self):
        """ Add a button to reset the State Variables to their default values. """

        self.reset_sv_button = widgets.Button(description='Reset state-variables',
                                              disabled=False,
                                              layout=self.button_layout)

        def reset_state_variables(_):
            for sv in range(self.model.nvar):
                sv_str = self.model.state_variables[sv]
                self.sv_sliders[sv_str].value = self.sv_sliders_values[sv_str]

        self.reset_sv_button.on_click(reset_state_variables)

    def add_reset_param_button(self):
        """ Add a button to reset the model parameters to their default values. """

        self.reset_param_button = widgets.Button(description='Reset model params',
                                                 disabled=False,
                                                 layout=self.button_layout)

        def reset_parameters(_):
            for param_slider in self.param_sliders:
                self.param_sliders[param_slider].value = self.param_sliders_values[param_slider]

        self.reset_param_button.on_click(reset_parameters)

    def add_reset_noise_button(self):
        """ Add a button to reset integrator noise. """
        reset_noise_button = widgets.Button(description='Reset noise strength',
                                            disabled=False, layout=self.button_layout)

        def reset_noise(_):
            for slider in self.noise_sliders:
                slider.value = self.noise_slider_valinit

        reset_noise_button.on_click(reset_noise)
        return reset_noise_button

    def add_reset_random_stream_button(self):
        """ Add a button to reset random stream of Integrator Noise. """
        reset_seed_button = widgets.Button(description='Reset random stream',
                                           disabled=False, layout=self.button_layout)

        def reset_seed(_):
            self.integrator.noise.reset_random_stream()
            for slider in self.noise_sliders:
                slider.value = self.noise_slider_valinit

        reset_seed_button.on_click(reset_seed)
        return reset_seed_button

    def add_axes_sliders(self):
        """ Add sliders to set phase plane axes values. """

        default_range_x = (self.model.state_variable_range[self.svx][1] -
                           self.model.state_variable_range[self.svx][0])
        default_range_y = (self.model.state_variable_range[self.svy][1] -
                           self.model.state_variable_range[self.svy][0])
        min_val_x = self.model.state_variable_range[self.svx][0] - 4.0 * default_range_x
        max_val_x = self.model.state_variable_range[self.svx][1] + 4.0 * default_range_x
        min_val_y = self.model.state_variable_range[self.svy][0] - 4.0 * default_range_y
        max_val_y = self.model.state_variable_range[self.svy][1] + 4.0 * default_range_y

        self.sl_x_min_initval = self.model.state_variable_range[self.svx][0]
        self.sl_x_max_initval = self.model.state_variable_range[self.svx][1]
        self.sl_y_min_initval = self.model.state_variable_range[self.svy][0]
        self.sl_y_max_initval = self.model.state_variable_range[self.svy][1]

        self.sl_x_min = widgets.FloatSlider(description="xlo",
                                            min=min_val_x,
                                            max=max_val_x,
                                            value=self.model.state_variable_range[self.svx][0],
                                            layout=self.slider_layout,
                                            style=self.slider_style)

        def update_sl_x_range(_val):
            """ Update the x_min slider's max value to be equal to the min value of x_max slider. """

            self.sl_x_min.max = self.sl_x_max.value

        self.sl_x_min.observe(update_sl_x_range, 'value')

        self.sl_x_max = widgets.FloatSlider(description="xhi",
                                            min=min_val_x,
                                            max=max_val_x,
                                            value=self.model.state_variable_range[self.svx][1],
                                            layout=self.slider_layout,
                                            style=self.slider_style)

        self.sl_y_min = widgets.FloatSlider(description="ylo",
                                            min=min_val_y,
                                            max=max_val_y,
                                            value=self.model.state_variable_range[self.svy][0],
                                            layout=self.slider_layout,
                                            style=self.slider_style)

        def update_sl_y_range(_val):
            """ Update the y_min slider's max value to be equal to the min value of y_max slider. """

            self.sl_y_min.max = self.sl_y_max.value

        self.sl_y_min.observe(update_sl_y_range, 'value')

        self.sl_y_max = widgets.FloatSlider(description="yhi",
                                            min=min_val_y,
                                            max=max_val_y,
                                            value=self.model.state_variable_range[self.svy][1],
                                            layout=self.slider_layout,
                                            style=self.slider_style)

        self.params['sl_x_min'] = self.sl_x_min
        self.params['sl_x_max'] = self.sl_x_max
        self.params['sl_y_min'] = self.sl_y_min
        self.params['sl_y_max'] = self.sl_y_max

    def add_sv_sliders(self):
        """ Add sliders to set the Phase Plane State Variables values. """

        msv_range = self.model.state_variable_range
        self.sv_sliders = dict()
        self.sv_sliders_values = dict()
        for sv in range(self.model.nvar):
            sv_str = self.model.state_variables[sv]
            self.sv_sliders[sv_str] = widgets.FloatSlider(description=sv_str,
                                                          min=msv_range[sv_str][0],
                                                          max=msv_range[sv_str][1],
                                                          value=self.default_sv[sv, 0, 0],
                                                          layout=self.slider_layout,
                                                          style=self.slider_style)
            self.sv_sliders_values[sv_str] = self.default_sv[sv, 0, 0]
            self.params[sv_str] = self.sv_sliders[sv_str]

    def add_param_sliders(self):
        """ Add sliders to select the model parameter values. """

        self.param_sliders = dict()
        self.param_sliders_values = dict()

        for param_name in type(self.model).declarative_attrs:
            param_def = getattr(type(self.model), param_name)
            if not isinstance(param_def, NArray) or param_def.dtype != np.float_:
                continue
            param_range = param_def.domain
            if param_range is None:
                continue
            param_value = getattr(self.model, param_name)[0]
            diff = param_range.hi - param_range.lo
            self.param_sliders[param_name] = widgets.FloatSlider(description=param_name,
                                                                 min=param_range.lo,
                                                                 max=param_range.hi,
                                                                 step=param_range.step if param_range.step < diff else diff,
                                                                 value=param_value,
                                                                 layout=self.slider_layout,
                                                                 style=self.slider_style)
            self.param_sliders_values[param_name] = param_value
            self.params[param_name] = self.param_sliders[param_name]

    def add_noise_sliders(self):
        """ Add a slider to set integrator noise. """

        self.noise_sliders = []
        for state_variable in self.model.state_variables:
            ns = widgets.FloatSlider(description=state_variable,
                                                    min=0.0,
                                                    max=2.0,
                                                    step=0.01,
                                                    value=self.noise_slider_valinit,
                                                    layout=self.slider_layout,
                                                    style=self.slider_style)
            self.noise_sliders.append(ns)
            param = 'noise_slider_' + str(state_variable)
            self.params[param] = ns

    def add_integrator_widgets(self):
        """ Add a noise slider, reset noise button and reset random stream button for Stochastic Integrator. """

        if isinstance(self.integrator, integrators.IntegratorStochastic):
            if self.integrator.noise.ntau > 0.0:
                self.integrator.noise.configure_coloured(self.integrator.dt,
                                                         (1, self.model.nvar, 1, self.model.number_of_modes))
            else:
                self.integrator.noise.configure_white(self.integrator.dt,
                                                      (1, self.model.nvar, 1, self.model.number_of_modes))

            self.add_noise_sliders()
            reset_noise_button = self.add_reset_noise_button()
            reset_seed_button = self.add_reset_random_stream_button()
            return self.noise_sliders + [reset_noise_button, reset_seed_button]
        return []

    def add_mode_selector(self):
        """ Add a Radio Button to select the mode of model to be displayed. """

        self.mode_tuple = tuple(range(self.model.number_of_modes))
        self.mode_selector = widgets.Dropdown(options=self.mode_tuple, value=0, layout=self.other_layout)
        self.params['mode'] = self.mode_selector

    def add_sv_selector(self):
        """ Add a Dropdown list to select the State Variable for Each Axis. """

        # State variable for the X axis
        self.state_variable_x = widgets.Dropdown(options=list(self.model.state_variables), value=self.svx,
                                                 layout=self.other_layout)
        self.params['svx'] = self.state_variable_x
        self.state_variable_x.observe(self.update_axis_sliders, 'value')

        # State variable for the Y axis
        self.state_variable_y = widgets.Dropdown(options=list(self.model.state_variables), value=self.svy,
                                                 layout=self.other_layout)
        self.state_variable_y.observe(self.update_axis_sliders, 'value')
        self.params['svy'] = self.state_variable_y
        self.sv_sliders[self.state_variable_x.value].disabled = True
        self.sv_sliders[self.state_variable_y.value].disabled = True

    def add_traj_coords_text(self):
        """
        Add a Textbox to enter coordinate values for plotting trajectories.
        Add a button to clear trajectories.
        """
        self.traj_label = widgets.Label('Trajectory Coordinates (Float)')
        self.plot_traj = widgets.Valid(value=False, description="Hidden Field for Plotting Trajectory")
        self.clear_traj = widgets.Valid(value=False, description="Hidden Field for Clearing Trajectory")
        self.traj_out = widgets.Textarea(value='', placeholder='Trajectory Co-ordinates output will be shown here')

        def update_traj_text(_):
            self.traj_out.value = f'{self.traj_out.value}Trajectory plotted at ({self.traj_x.value},{self.traj_y.value}).\n'
            self.plot_traj.value = True
            self.clear_traj.value = False

        def disable_plot_traj(_):
            self.plot_traj.value = False

        def clear_plotted_traj(_):
            self.traj_out.value = ''
            self.clear_traj.value = True
            self.plot_traj.value = False

        self.traj_x_label = widgets.Label('X: ')
        self.traj_x = widgets.FloatText(placeholder='X - Coordinate')
        self.traj_x.observe(disable_plot_traj, 'value')
        self.traj_x_box = widgets.HBox([self.traj_x_label, self.traj_x])

        self.traj_y_label = widgets.Label('Y: ')
        self.traj_y = widgets.FloatText(placeholder='Y - Coordinate')
        self.traj_y.observe(disable_plot_traj, 'value')
        self.traj_y_box = widgets.HBox([self.traj_y_label, self.traj_y])

        self.plot_traj_button = widgets.Button(description='Plot Trajectory')
        self.plot_traj_button.on_click(update_traj_text)

        self.clear_traj_button = widgets.Button(description='Clear Trajectories')
        self.clear_traj_button.on_click(clear_plotted_traj)

        self.params['traj_x'] = self.traj_x
        self.params['traj_y'] = self.traj_y
        self.params['plot_traj'] = self.plot_traj
        self.params['clear_traj'] = self.clear_traj

    def set_state_vector(self):
        """ Set up the default state-variable values. """

        self.sv_mean = np.array([self.model.state_variable_range[key].mean() for key in self.model.state_variables])
        self.sv_mean = self.sv_mean.reshape((self.model.nvar, 1, 1))
        self.default_sv = self.sv_mean.repeat(self.model.number_of_modes, axis=2)
        self.no_coupling = np.zeros((self.model.nvar, 1, self.model.number_of_modes))

    # ------------------------------------------------------------------------#
    # ------------------- Functions for updating the figure ------------------#
    # ------------------------------------------------------------------------#

    def set_default_axes_sliders(self):
        """ Calculate the default X Axis and Y Axis Sliders values. """

        default_range_x = (self.model.state_variable_range[self.state_variable_x.value][1] -
                           self.model.state_variable_range[self.state_variable_x.value][0])
        default_range_y = (self.model.state_variable_range[self.state_variable_y.value][1] -
                           self.model.state_variable_range[self.state_variable_y.value][0])
        min_val_x = self.model.state_variable_range[self.state_variable_x.value][0] - 4.0 * default_range_x
        max_val_x = self.model.state_variable_range[self.state_variable_x.value][1] + 4.0 * default_range_x
        min_val_y = self.model.state_variable_range[self.state_variable_y.value][0] - 4.0 * default_range_y
        max_val_y = self.model.state_variable_range[self.state_variable_y.value][1] + 4.0 * default_range_y

        return min_val_x, max_val_x, min_val_y, max_val_y

    def update_axis_sliders(self, _):
        """ Update the Axes Sliders to their default values when State Variable is changed. """

        self.sl_x_min_initval = self.model.state_variable_range[self.state_variable_x.value][0]
        self.sl_x_max_initval = self.model.state_variable_range[self.state_variable_x.value][1]
        self.sl_y_min_initval = self.model.state_variable_range[self.state_variable_y.value][0]
        self.sl_y_max_initval = self.model.state_variable_range[self.state_variable_y.value][1]

        min_val_x, max_val_x, min_val_y, max_val_y = self.set_default_axes_sliders()

        self.sl_x_min.min = min_val_x
        self.sl_x_min.value = self.sl_x_min_initval
        self.sl_x_min.max = max_val_x
        self.sl_x_max.min = min_val_x
        self.sl_x_max.value = self.sl_x_max_initval
        self.sl_x_max.max = max_val_x

        self.sl_y_min.min = min_val_y
        self.sl_y_min.value = self.sl_y_min_initval
        self.sl_y_min.max = max_val_y

        self.sl_y_max.min = min_val_y
        self.sl_y_max.value = self.sl_y_max_initval
        self.sl_y_max.max = max_val_y

        for slider in self.sv_sliders.values():
            slider.disabled = False
        self.sv_sliders[self.state_variable_x.value].disabled = True
        self.sv_sliders[self.state_variable_y.value].disabled = True

    def _add_model_selector(self):
        models = {}

        for model in models_module.ModelsEnum.get_base_model_subclasses():
            if model._nvar >= 2:
                models[model.__name__] = model

        self.model_selector = widgets.Dropdown(options=models.keys(),
                                               description='Model:',
                                               value=self.model.__class__.__name__,
                                               disabled=self.disable_model_dropdown)

        # on change callback
        def change_model(change):
            if change['type'] != 'change' or change['name'] != 'value':
                return

            self.model = models[change['new']]()
            # Reset model
            self.svx = self.model.state_variables[0]  # x-axis: 1st state variable
            self.svy = self.model.state_variables[1]  # y-axis: 2nd state variable
            self._rebuild_widget()

        self.model_selector.observe(change_model)

    def _add_integrator_selector(self):
        integrators_dict = IntegratorsEnum.get_integrators_dict()
        self.integrator_selector = widgets.Dropdown(options=integrators_dict.keys(),
                                                    description='Integrator',
                                                    value=self.integrator.__class__.__name__)

        def on_change_callback(change):
            if change['type'] != 'change' or change['name'] != 'value':
                return
            self.integrator = integrators_dict[change['new']]()
            if hasattr(self.integrator, 'noise'):
                self.noise_slider_valinit = self.integrator.noise.nsig[0]
                self._rebuild_widget()
            else:
                self.message_area.value = f"{self.integrator.__class__.__name__} integrator has no noise parameter."
        self.integrator_selector.observe(on_change_callback)

    def _rebuild_widget(self):
        # type: () -> None
        """
        rebuilds widget. Used when changing model or integrator
        """
        for wid in self.hbox.children:
            wid.close()

        self.message_area.value = ""
        self.model.configure()
        self.ui = self.create_ui()
        self.clear_traj.value = True
        self.out = widgets.interactive_output(self.plotter, self.params)
        self.hbox.children = (self.ui, self.out)

    # -----------------------------------------------------------#
    # ----------------- EXPORT FUNCTIONALITY --------------------#
    # -----------------------------------------------------------#

    def build_export_section(self):
        """
        Builds UI for Exports tab
        """
        btn_tooltip = 'Creates a .py file with code needed to generate a model instance ' \
                      'or a json file with model params'
        export_types = [choice.value for choice in list(ModelConfigurationExports)]
        self.export_type = widgets.Dropdown(options=export_types,
                                            value=export_types[0],
                                            description='Export as:',
                                            disabled=self.disable_export_dropdown
                                            )
        self.do_export_btn = widgets.Button(description='Export model configuration',
                                            layout=self.button_layout,
                                            icon='file-export',
                                            tooltip=btn_tooltip,
                                            disabled=False)
        self.config_name = widgets.Text(placeholder='Config name',
                                        value=self.export_filename or '',
                                        disabled=self.export_filename is not None)
        self.do_export_btn.on_click(self.export_model_configuration)
        self.py_output = widgets.Textarea(value='Code to generate model instance will appear here')
        info = widgets.HTML(value="<p>*You can export the code to instantiate this widget's model<br/> with the "
                                  "current parameters directly in a cell by calling <br/> "
                                  "export_model() on this widget.</p>")
        self.export_model_section = widgets.VBox((self.export_type, self.config_name,
                                                  self.do_export_btn, self.py_output, info))

    def export_model_configuration(self, *_args):
        # type: (any) -> None
        """
        on click handler for model configuration export
        args are not used since the handlers are passed the buttons as args by default
        """
        export_type = self.export_type.value
        model = self.model
        keys = self.param_sliders.keys()
        exporter = model_exporter_factory(export_type, model, keys, self.export_filename)
        if self.config_name.value.strip():
            exporter.config_name = self.config_name.value
        exporter.do_export()
        if isinstance(exporter, PythonCodeExporter):
            self.py_output.value = exporter.get_instance_code()

    def export_model(self):
        """
        exports model instance as code in a new notebook cell
        !!! Only works if it is called in a notebook cell. If called otherwise
        the cell with code will be generated only after a cell rerun
        """
        exporter = PythonCodeExporter(self.model, self.param_sliders.keys())
        code = exporter.get_instance_code()
        shell = get_ipython()
        shell.payload_manager.write_payload(dict(source='set_next_input',
                                                 text=code,
                                                 replace=False))

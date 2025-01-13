# -*- coding: utf-8 -*-
#
# "TheVirtualBrain - Widgets" package
#
# (c) 2022-2025, TVB Widgets Team
#

import threading
import numpy as np
import ipywidgets as widgets
from tvb.basic.neotraits.api import NArray
from tvb.simulator.simulator import Simulator
from tvbwidgets.core.hpc.config import HPCConfig
from tvbwidgets.core.hpc.launcher import HPCLaunch
from tvbwidgets.core.pse.parameters import launch_local_param
from tvbwidgets.core.pse.parameters import METRICS
from tvbwidgets.ui.base_widget import TVBWidget
from IPython.core.display_functions import display


class PSELauncher(TVBWidget):

    def __init__(self, simulator, connectivity_list=None, hpc_config=None):
        # type: (Simulator, list, HPCConfig) -> None
        super().__init__()
        self.simulator = simulator
        self.connectivity_list = connectivity_list
        self.hpc_config = hpc_config
        self.metrics = METRICS
        self.params_dict = {}
        self.create_dict()
        self.param_1 = None
        self.param_2 = None
        self.message_area = None
        self.min_range1 = None
        self.max_range1 = None
        self.step1 = None
        self.min_range2 = None
        self.max_range2 = None
        self.step2 = None
        self.launch_local_button = None
        self.launch_hpc_button = None
        self.file_name = None
        self.metrics_sm = None
        self.progress = None
        self.progress_lock = threading.Lock()
        self._create_infos()
        self.handle_launch_buttons()
        self.create_metrics()
        self.file_options()
        widget = self.create_params()
        display(widget)

    def create_dict(self):
        for elem in type(self.simulator.model).declarative_attrs:
            attribute = getattr(type(self.simulator.model), elem)
            if isinstance(attribute, NArray) and attribute.domain is not None:
                self.params_dict[f"model.{elem}"] = [attribute.domain.lo, attribute.domain.hi, attribute.domain.step]

        for elem in type(self.simulator.coupling).declarative_attrs:
            attribute = getattr(type(self.simulator.coupling), elem)
            if isinstance(attribute, NArray) and attribute.domain is not None:
                self.params_dict[f"coupling.{elem}"] = [attribute.domain.lo, attribute.domain.hi, attribute.domain.step]

        cond_speed_default_value = self.simulator.conduction_speed
        self.params_dict["conduction_speed"] = [0, 10 * cond_speed_default_value, cond_speed_default_value]

        if "noise" in type(self.simulator.integrator).declarative_attrs:
            for elem in type(self.simulator.integrator.noise).declarative_attrs:
                attribute = getattr(type(self.simulator.integrator.noise), elem)
                if isinstance(attribute, NArray) and attribute.domain is not None:
                    self.params_dict[f"integrator.{elem}"] = [attribute.domain.lo, attribute.domain.hi,
                                                              attribute.domain.step]

        if self.connectivity_list is not None:
            self.params_dict["connectivity"] = [0, 0, 0]

    def file_options(self):
        self.file_name = widgets.Text(
            placeholder='Type here',
            description="Name of file",
            disabled=False
        )

    def _prepare_launch(self, where="Local"):
        self._update_info_message(f"{where} launch in progress ...")
        x_values = self.compute_params_values(self.param_1.value)
        y_values = self.compute_params_values(self.param_2.value)
        file_name = self.verify_file_name()
        self.progress.min = 0
        self.progress.max = len(x_values) * len(y_values) + 1  # no of simulations + 1 for preparation step
        self.update_progress(0)
        return file_name, x_values, y_values

    def handle_launch_buttons(self):
        self.launch_local_button = widgets.Button(
            description='Local launch',
            disabled=False,
            button_style='success',
        )

        self.launch_hpc_button = widgets.Button(
            description='HPC launch',
            disabled=self.hpc_config is None,
            button_style='success',
        )

        def hpc_launch(_change):
            if self.launch_hpc_button.button_style == "success":
                file_name, x_values, y_values = self._prepare_launch("HPC")
                HPCLaunch(self.simulator, self.hpc_config, self.param_1.value, self.param_2.value, x_values, y_values,
                          list(self.metrics_sm.value), file_name, self.update_progress)
                self._update_info_message("PSE completed! ")

        def local_launch(_change):
            self.logger.info("Local launch in progress")
            if self.launch_local_button.button_style == "success":
                file_name, x_values, y_values = self._prepare_launch("Local")
                launch_local_param(self.simulator, self.param_1.value, self.param_2.value, x_values, y_values,
                                   list(self.metrics_sm.value), file_name, self.update_progress)
                self._update_info_message("PSE completed! ")

        self.launch_hpc_button.on_click(hpc_launch)
        self.launch_local_button.on_click(local_launch)

    def compute_params_values(self, param):
        if param == "connectivity":
            return self.connectivity_list
        else:
            if param == self.param_1.value:
                return self.create_input_values(self.min_range1.value, self.max_range1.value, self.step1.value)
            else:
                return self.create_input_values(self.min_range2.value, self.max_range2.value, self.step2.value)

    def verify_file_name(self):
        file_name = self.file_name.value
        if file_name == "":
            self.logger.info("A file name was not specified. It will be created under the name 'test.h5'.")
            return "test.h5"
        elif ".h5" not in file_name:
            return f"{file_name}.h5"
        else:
            return file_name

    def update_progress(self, jobs_completed=None, error_msg=None):
        if error_msg is not None:
            self._update_info_message(error_msg, is_error=True)

        with self.progress_lock:
            if jobs_completed is None:
                self.progress.value += 1
            elif jobs_completed >= 0:
                self.progress.value = jobs_completed + 1

    def create_metrics(self):
        self.metrics_sm = widgets.SelectMultiple(
            options=self.metrics,
            description="Metrics",
            value=[self.metrics[0]],
            disabled=False, layout=widgets.Layout(margin="0px 20px 10px 25px", height="115px", width="340px"))

    def _create_infos(self):
        self.title = widgets.HTML(value="<font color='navyblue' size='4'>PSE Launcher</font>",
                                  layout=widgets.Layout(margin="0px 0px 0px 20px"))
        self.message_area = widgets.HTML(value="<p></p>", layout=widgets.Layout(margin="0px 0px 0px 20px"))
        self.progress = widgets.IntProgress(value=0, min=0, max=100, description='Progress:',
                                            style={'description_width': '60px'}, orientation='horizontal')

    def _update_info_message(self, message, is_error=False):
        self.message_area.value = f"<p><b><font color='{'red' if is_error else 'green'}'>{message}</font></b></p>"

    @staticmethod
    def create_input_values(min_value, max_value, step):
        values = []
        for elem in np.arange(min_value, max_value, step):
            values.append(elem)
        return values

    def create_params(self):
        self.param_1 = widgets.Dropdown(
            options=sorted(self.params_dict.keys()),
            description="Param 1",
            value=list(sorted(self.params_dict.keys()))[0],
            disabled=False
        )
        self.param_2 = widgets.Dropdown(
            options=sorted(self.params_dict.keys()),
            description="Param 2",
            value=list(sorted(self.params_dict.keys()))[2],
            disabled=False
        )

        def param_changed(change):
            if change['type'] != 'change' or change['name'] != 'value':
                return

            if self.param_1.value != self.param_2.value:
                self._update_info_message("")
                self.launch_hpc_button.button_style = 'success'
                self.launch_local_button.button_style = 'success'
            else:
                self._update_info_message("The parameters should be different!", True)
                self.launch_hpc_button.button_style = 'danger'
                self.launch_local_button.button_style = 'danger'

            if self.param_1.value == change['new'] and self.param_1.value != self.param_2.value:
                if self.param_1.value == "connectivity":
                    self.visibility_range(True, "hidden")
                elif change['old'] == "connectivity":
                    self.visibility_range(True, "visible")

                self.change_range_param(True)
            elif self.param_2.value == change['new'] and self.param_1.value != self.param_2.value:
                if self.param_2.value == "connectivity":
                    self.visibility_range(False, "hidden")
                elif change['old'] == "connectivity":
                    self.visibility_range(False, "visible")

                self.change_range_param(False)
            else:
                if self.param_1.value == "connectivity":
                    self.visibility_range(True, "hidden")
                    self.visibility_range(False, "hidden")
                else:
                    self.visibility_range(True, "visible")
                    self.visibility_range(False, "visible")
                self.change_range_param(True)
                self.change_range_param(False)

        self.param_1.observe(param_changed)
        self.param_2.observe(param_changed)

        return self._init_range_params()

    def visibility_range(self, param1, visibility):
        if param1:
            self.min_range1.layout.visibility = visibility
            self.max_range1.layout.visibility = visibility
            self.step1.layout.visibility = visibility
        else:
            self.min_range2.layout.visibility = visibility
            self.max_range2.layout.visibility = visibility
            self.step2.layout.visibility = visibility

    def change_range_param(self, param1):
        if param1:
            self.min_range1.value = self.params_dict[self.param_1.value][0]
            self.max_range1.value = self.params_dict[self.param_1.value][1]
            self.step1.value = self.params_dict[self.param_1.value][2]
        else:
            self.min_range2.value = self.params_dict[self.param_2.value][0]
            self.max_range2.value = self.params_dict[self.param_2.value][1]
            self.step2.value = self.params_dict[self.param_2.value][2]

    def _init_range_params(self):
        self.min_range1, self.max_range1, self.step1, param_box1 = self._build_for_param(self.param_1)
        self.min_range2, self.max_range2, self.step2, param_box2 = self._build_for_param(self.param_2)

        buttons_box = widgets.VBox(
            children=[self.launch_local_button, self.launch_hpc_button, self.progress],
            layout=widgets.Layout(margin="0px 0px 50px 20px"))

        metrics_buttons_box = widgets.HBox(children=[self.metrics_sm, self.file_name, buttons_box],
                                           layout=widgets.Layout(margin="20px 0px 0px 0px"))
        return widgets.VBox(children=[self.title, self.message_area, param_box1, param_box2, metrics_buttons_box],
                            layout=self.DEFAULT_BORDER)

    def _build_for_param(self, param_current):
        min_input = widgets.FloatText(
            value=self.params_dict[param_current.value][0],
            description="Min range",
            disable=False
        )

        max_input = widgets.FloatText(
            value=self.params_dict[param_current.value][1],
            description="Max range",
            disable=False
        )

        step_input = widgets.FloatText(
            value=self.params_dict[param_current.value][2],
            description="Step",
            disable=False
        )

        range_box = widgets.VBox(children=[min_input, max_input, step_input],
                                 layout=widgets.Layout(margin="0px 0px 0px 40px"))

        param_box = widgets.HBox(children=[param_current, range_box],
                                 layout=widgets.Layout(margin="20px 0px 0px 40px"))

        return min_input, max_input, step_input, param_box

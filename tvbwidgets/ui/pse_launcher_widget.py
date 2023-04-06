# -*- coding: utf-8 -*-
#
# "TheVirtualBrain - Widgets" package
#
# (c) 2022-2023, TVB Widgets Team
#
import numpy as np
from tvb.basic.neotraits._attr import NArray
from tvbwidgets.core.pse.parameters import launch_local_param
from tvbwidgets.core.pse.parameters import METRICS
from tvbwidgets.ui.base_widget import TVBWidget
from IPython.core.display_functions import display
import ipywidgets as widgets


class PSELauncher(TVBWidget):

    def __init__(self, simulator, connectivity_list=None):
        # type: (Simulator, list) -> None
        super().__init__()
        self.simulator = simulator
        self.connectivity_list = connectivity_list
        self.metrics = METRICS
        self.params_dict = {}
        self.create_dict()
        self.param_1 = None
        self.param_2 = None
        self.warning = None
        self.launch_text_information = None
        self.min_range1 = None
        self.max_range1 = None
        self.step1 = None
        self.min_range2 = None
        self.max_range2 = None
        self.step2 = None
        self.launch_local_button = None
        self.file_name = None
        self.metrics_sm = None
        self.create_informative_texts()
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
            description="<b>Name of file</b>",
            disabled=False
        )

    def handle_launch_buttons(self):
        self.launch_local_button = widgets.Button(
            description='Local launch',
            disabled=False,
            button_style='success',
        )

        def local_launch(change):
            self.logger.info("Local launch in progress")
            if self.launch_local_button.button_style == "success":
                self.launch_text_information.value = "<font color='gray'>Local launch in progress"

                if self.param_1.value == "connectivity":
                    x_values = self.connectivity_list
                else:
                    x_values = self._create_input_values(self.min_range1.value, self.max_range1.value, self.step1.value)
                if self.param_2.value == "connectivity":
                    y_values = self.connectivity_list
                else:
                    y_values = self._create_input_values(self.min_range2.value, self.max_range2.value, self.step2.value)
                launch_local_param(self.simulator, self.param_1.value, self.param_2.value, x_values, y_values,
                                   list(self.metrics_sm.value), self.file_name.value)

        self.launch_local_button.on_click(local_launch)

    def create_metrics(self):
        self.metrics_sm = widgets.SelectMultiple(
            options=self.metrics,
            description="<b>Metrics</b>",
            value=[self.metrics[0]],
            disabled=False, layout=widgets.Layout(margin="0px 20px 10px 25px", height="115px", width="340px"))

    def create_informative_texts(self):
        self.warning = widgets.HTML(value="", layout=widgets.Layout(margin="0px 0px 0px 65px"))
        self.launch_text_information = widgets.HTML(value="", layout=widgets.Layout(margin="7px 0px 0px 8px"))

    def _create_input_values(self, min_value, max_value, step):
        return np.arange(min_value, max_value, step).tolist()

    def create_params(self):
        self.param_1 = widgets.Dropdown(
            options=sorted(self.params_dict.keys()),
            description="<b>PSE param1</b>",
            value=list(sorted(self.params_dict.keys()))[0],
            disabled=False
        )
        self.param_2 = widgets.Dropdown(
            options=sorted(self.params_dict.keys()),
            description="<b>PSE param2</b>",
            value=list(sorted(self.params_dict.keys()))[2],
            disabled=False
        )

        def param_changed(change):
            if change['type'] != 'change' or change['name'] != 'value':
                return

            if self.param_1.value != self.param_2.value:
                self.warning.value = ""
                self.launch_local_button.button_style = 'success'
            else:
                self.warning.value = "<b><font color='red'>The parameters should be different!</b>"
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

        return self.pse_params_range()

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

    def pse_params_range(self):
        self.set_range()

        range1 = widgets.VBox(children=[self.min_range1, self.max_range1, self.step1],
                              layout=widgets.Layout(margin="0px 0px 0px 60px"))
        range2 = widgets.VBox(children=[self.min_range2, self.max_range2, self.step2],
                              layout=widgets.Layout(margin="0px 0px 0px 60px"))
        param_box1 = widgets.HBox(children=[self.param_1, range1], layout=widgets.Layout(margin="40px 0px 0px 50px"))
        param_box2 = widgets.HBox(children=[self.param_2, range2], layout=widgets.Layout(margin="30px 0px 0px 50px"))
        buttons_box = widgets.VBox(
            children=[self.launch_local_button, self.launch_text_information],
            layout=widgets.Layout(
                margin="0px 0px 50px 20px"))

        metrics_buttons_box = widgets.HBox(children=[self.metrics_sm, self.file_name, buttons_box],
                                           layout=widgets.Layout(margin="40px "
                                                                        "0px "
                                                                        "30px "
                                                                        "3px"))
        return widgets.VBox(children=[self.warning, param_box1, param_box2, metrics_buttons_box],
                            layout=self.DEFAULT_BORDER)

    def set_range(self):
        self.min_range1 = widgets.FloatText(
            value=self.params_dict[self.param_1.value][0],
            description="<b><font color='gray'>Min range</b>",
            disable=False
        )

        self.max_range1 = widgets.FloatText(
            value=self.params_dict[self.param_1.value][1],
            description="<b><font color='gray'>Max range</b>",
            disable=False
        )

        self.step1 = widgets.FloatText(
            value=self.params_dict[self.param_1.value][2],
            description="<b><font color='gray'>Step</b>",
            disable=False
        )

        self.min_range2 = widgets.FloatText(
            value=self.params_dict[self.param_2.value][0],
            description="<b><font color='gray'>Min range</b>",
            disable=False
        )

        self.max_range2 = widgets.FloatText(
            value=self.params_dict[self.param_2.value][1],
            description="<b><font color='gray'>Max range</b>",
            disable=False
        )

        self.step2 = widgets.FloatText(
            value=self.params_dict[self.param_2.value][2],
            description="<b><font color='gray'>Step</b>",
            disable=False
        )

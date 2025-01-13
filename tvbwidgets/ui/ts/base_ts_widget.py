# -*- coding: utf-8 -*-
#
# "TheVirtualBrain - Widgets" package
#
# (c) 2022-2025, TVB Widgets Team
#

import math
import numpy as np
import ipywidgets as widgets
from tvb.datatypes.time_series import TimeSeries

from tvbwidgets.core.exceptions import InvalidInputException
from tvbwidgets.ui.base_widget import TVBWidget
from tvbwidgets.ui.ts.data_wrappers.tvb_data_wrapper import WrapperTVB
from tvbwidgets.ui.ts.data_wrappers.numpy_data_wrapper import WrapperNumpy


class TimeSeriesWidgetBase(widgets.VBox, TVBWidget):
    # =========================================== SETUP ================================================================
    def add_datatype(self, ts_tvb):
        # type: (TimeSeries) -> None
        data_wrapper = WrapperTVB(ts_tvb)
        self.logger.debug("Adding TVB TS for display...")
        self._populate_from_data_wrapper(data_wrapper)

    def add_data_array(self, numpy_array, sample_freq, ch_idx):
        # type: (np.array, float, int) -> None
        data_wrapper = WrapperNumpy(numpy_array, sample_freq, ch_idx=ch_idx)
        self._populate_from_data_wrapper(data_wrapper)

    def add_data(self, data, sample_freq=None, ch_idx=None):
        if isinstance(data, TimeSeries):
            self.add_datatype(data)
        else:
            self.add_data_array(data, sample_freq, ch_idx)

    def _populate_from_data_wrapper(self, data_wrapper):
        # type: (ABCDataWrapper) -> None
        if self.data is not None:
            raise InvalidInputException("TSWidget is not yet capable to display more than one TS, "
                                        "either use wid.reset_data, or create another widget instance!")

        self.data = data_wrapper
        self.sample_freq = data_wrapper.get_ts_sample_rate()
        self.displayed_period = data_wrapper.get_ts_period()
        self.ch_names, self.ch_order, self.ch_types = data_wrapper.get_channels_info()
        self.raw = self.data.build_raw()

    # ======================================== CHANNELS  ==============================================================
    def _unselect_all(self, _):
        self.logger.debug("Unselect all was called!")
        for cb_name in self.checkboxes:
            self.checkboxes[cb_name].value = False

    def _select_all(self, _):
        self.logger.debug("Select all was called!")
        for cb_name in self.checkboxes:
            self.checkboxes[cb_name].value = True

    def _create_checkboxes(self, array_wrapper, no_checkbox_columns=2):
        checkboxes_list, checkboxes_stack = [], []
        labels = array_wrapper.get_channels_info()[0]
        cb_per_col = math.ceil(len(labels) / no_checkbox_columns)  # number of checkboxes in a column
        for i, label in enumerate(labels):
            self.checkboxes[label] = widgets.Checkbox(value=True, description=label, indent=False,
                                                      layout=widgets.Layout(width='max-content'))
            if i and i % cb_per_col == 0:
                checkboxes_list.append(widgets.VBox(children=checkboxes_stack))
                checkboxes_stack = []
            checkboxes_stack.append(self.checkboxes[label])
        checkboxes_list.append(widgets.VBox(children=checkboxes_stack))
        checkboxes_region = widgets.HBox(children=checkboxes_list)
        return checkboxes_region

    def _create_select_unselect_all_buttons(self):
        select_all_btn = widgets.Button(description="Select all", layout=self.BUTTON_STYLE)
        select_all_btn.on_click(self._select_all)
        unselect_all_btn = widgets.Button(description="Unselect all", layout=self.BUTTON_STYLE)
        unselect_all_btn.on_click(self._unselect_all)
        return select_all_btn, unselect_all_btn

    def _create_dim_selection_buttons(self, array_wrapper):
        self.radio_buttons = []
        actions = []
        for idx, info in array_wrapper.extra_dimensions.items():
            extra_area, extra_radio_btn = self._create_selection(info[0], idx, dim_options=info[1])
            self.radio_buttons.append(extra_radio_btn)
            if extra_area is not None:
                actions.append(extra_area)

        return actions

    def _get_selection_values(self):
        sel1 = self.radio_buttons[0].value if self.radio_buttons[0] else None
        sel2 = self.radio_buttons[1].value if self.radio_buttons[1] else None
        return sel1, sel2

    def _create_selection(self, title="Mode", shape_pos=3, dim_options=None):
        if self.data is None or len(self.data.data_shape) <= max(2, shape_pos):
            return None, None

        no_dims = self.data.data_shape[shape_pos]
        if dim_options is None or dim_options == []:
            dim_options = [i for i in range(no_dims)]
        sel_radio_btn = widgets.RadioButtons(options=dim_options, layout={'width': 'max-content'})
        sel_radio_btn.observe(self._dimensions_selection_update, names=['value'])
        accordion = widgets.Accordion(children=[sel_radio_btn], selected_index=None, layout={'width': '20%'})
        accordion.set_title(0, title)
        return accordion, sel_radio_btn

    def _dimensions_selection_update(self, _):
        # update self.raw
        sel1, sel2 = self._get_selection_values()
        new_slice = self.data.get_update_slice(sel1, sel2)
        self.raw = self.data.build_raw(new_slice)

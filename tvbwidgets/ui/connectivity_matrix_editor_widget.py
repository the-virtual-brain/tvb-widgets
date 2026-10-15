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
import os
import numpy as np
import ipycanvas as canvas
import ipywidgets as widgets
import matplotlib.colors as mcolors
from IPython.display import display
from tvb.basic.exceptions import TVBException
from tvb.config.init.datatypes_registry import populate_datatypes_registry
from tvb.core.neocom import h5
from tvb.datatypes.connectivity import Connectivity

from tvbwidgets import get_logger
from tvbwidgets.core.simulator.model_exporters import is_valid_file_name
from tvbwidgets.ui.base_widget import TVBWidget

LOGGER = get_logger(__name__)

POPUP_CLASS = "matrix-editor-popup"
POPUP_ABOVE_CLASS = "matrix-editor-popup-above"
POPUP_STYLE = f"""<style>
.{POPUP_CLASS} {{ background-color: white; }}
.{POPUP_ABOVE_CLASS} {{ transform: translateY(-100%); }}
</style>"""
INVALID_NUMBER_MESSAGE = "Not a valid number. Original value is kept."
NOT_FINITE_MESSAGE = "Not a finite number. Original value is kept."
ERROR_COLOR = "#d32f2f"
SUCCESS_COLOR = "#2e7d32"
H5_EXTENSION = ".h5"
DEFAULT_EXPORT_NAME = "edited_connectivity"
INVALID_FILE_NAME_MESSAGE = "Use only letters, digits and _ in the file name."
FILE_EXISTS_MESSAGE = "{} already exists. Choose another name."
EXPORT_FAILED_MESSAGE = "Could not write {}."
EXPORT_SUCCESS_MESSAGE = "Exported {} to the notebook folder."


def format_message(message, color):
    return f'<div style="color:{color};font-size:11px;line-height:1.3;">{message}</div>'


def load_connectivity_h5(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"{file_path} does not exist.")
    # h5.load needs the TVB datatypes registry, which is empty after a kernel restart and needs to be filled first
    populate_datatypes_registry()
    return h5.load(file_path)


class ConnectivityMatrixEditor(TVBWidget):
    def __init__(self, connectivity, size=None, **kwargs):
        super().__init__(**kwargs)
        self.connectivity = connectivity
        self.num_rows = int(len(self.connectivity.weights[0]) / 2)  # num_cols will be equal to num_rows
        if size is None:
            size = self.num_rows * 20
        self.size = size
        self.layout_offset = self.size * 0.2

        self.new_connectivity = self._prepare_new_connectivity()
        self.header = widgets.HBox(layout=self.DEFAULT_BORDER)
        self._make_header()
        self.tab = widgets.Tab(layout=self.DEFAULT_BORDER)
        self._get_quadrant_range(selection=1)
        self._prepare_matrices_tab()

    def _make_header(self):
        options = ["Quadrant 1", "Quadrant 2", "Quadrant 3", "Quadrant 4"]

        self.quadrants = widgets.Dropdown(options=options)

        self.quadrants.observe(self._on_quadrant_select, names=["value"])

        self.export_message = widgets.HTML(value="", layout=widgets.Layout(margin="0 10px 0 auto",
                                                                             align_self="center"))
        self.export_name = widgets.Text(value=self._get_next_free_name(), layout=widgets.Layout(width="200px"))
        extension_label = widgets.Label(H5_EXTENSION)
        self.export_button = widgets.Button(description="Export H5", layout=widgets.Layout(width="100px"))
        self.export_button.on_click(self._on_click_export)

        self.header.children = [self.quadrants, self.export_message, self.export_name, extension_label,
                                self.export_button]
                                
    def _on_quadrant_select(self, change):
        self.popup.layout.visibility = "hidden"

        selection = int(change["new"][-1])

        self._get_quadrant_range(selection)
        self._update_matrices_view(self.new_connectivity)

    def _get_quadrant_range(self, selection):
        middle_val = int(self.connectivity.weights.shape[0] / 2)

        if selection == 1:
            from_row = 0
            from_col = 0
        elif selection == 2:
            from_row = middle_val
            from_col = 0
        elif selection == 3:
            from_row = 0
            from_col = middle_val
        else:
            from_row = middle_val
            from_col = middle_val

        # indexing starts from this row and col
        self.from_row = from_row
        self.from_col = from_col
    
    def _handle_tab_change(self, change):
        if self.popup.layout.visibility == 'visible':
            self.on_click_cancel()

    def _prepare_matrices_tab(self):
        self.weights_matrix = self._prepare_matrix("weights")
        self.tract_lengths_matrix = self._prepare_matrix("tract_lengths")

        self.weights_matrix.on_mouse_down(lambda x, y: self.on_cell_clicked(x, y, "weights"))
        self.weights_matrix.on_mouse_move(self.set_mouse_position)

        self.tract_lengths_matrix.on_mouse_down(lambda x, y: self.on_cell_clicked(x, y, "tract_lengths"))
        self.tract_lengths_matrix.on_mouse_move(self.set_mouse_position)

        self.tab.observe(self._handle_tab_change, names='selected_index')

        out1 = widgets.Output()
        out2 = widgets.Output()

        with out1:
            display(self.weights_matrix)

        with out2:
            display(self.tract_lengths_matrix)

        self.popup = widgets.VBox(
        layout=widgets.Layout(
            width='200px',
            padding='8px 10px',
            min_width='200px',
            visibility='hidden',
            border='4px solid black',
            z_index='10',
            position='absolute',
            align_self='flex-start',
            justify_content='center',
            align_items='center'
         )
        )
        self.popup_value = widgets.Text(layout=widgets.Layout(width="50%", margin="10px 0"))
        self.popup_error = widgets.HTML(value="", layout=widgets.Layout(width="100%", margin="0"))

        self.popup_change = widgets.Button(
            description="Change",
            layout=widgets.Layout(width="48%", margin="3px 0"),
            style={ 'font_weight': 'bold'}
        )

        self.popup_cancel = widgets.Button(
            description="Cancel",
            layout=widgets.Layout(width="48%", margin="3px 0"),
            style={'font_weight': 'bold'}
        )

        self.popup_buttons = widgets.HBox(
            [self.popup_change, self.popup_cancel],
            layout=widgets.Layout(
                justify_content='space-between',
                width="100%",
                margin="0"
            )
        )

        popup_style = widgets.HTML(POPUP_STYLE, layout=widgets.Layout(display="none"))
        self.popup.add_class(POPUP_CLASS)
        self.popup.children = [self.popup_value, self.popup_buttons, self.popup_error, popup_style]

        self.popup_change.on_click(self.on_apply_change)
        self.popup_cancel.on_click(self.on_click_cancel)

        scrollable_container_weights = widgets.Box(
            [widgets.Box([out1, self.popup], layout=widgets.Layout(position='relative'))],
            layout=widgets.Layout(
                width='1200px',
                height='600px',
                overflow_x='auto',
                overflow_y='auto',
            )
        )

        scrollable_container_tract = widgets.Box(
            [widgets.Box([out2, self.popup], layout=widgets.Layout(position='relative'))],
            layout=widgets.Layout(
                width='1200px',
                height='600px',
                overflow_x='auto',
                overflow_y='auto',
            )
        )

        container1 = widgets.Box([scrollable_container_weights])
        container2 = widgets.Box([scrollable_container_tract])
        self.tab.children = [container1, container2]
        self.tab.set_title(0, "weights")
        self.tab.set_title(1, "tract_lengths")

    def _prepare_matrix(self, matrix_name):
        matrix = getattr(self.connectivity, matrix_name)
        matrix_full = canvas.MultiCanvas(6, width=self.size * 1.5, height=self.size * 1.2)

        matrix_view = matrix_full[0]
        row_header = matrix_full[1]
        column_header = matrix_full[2]
        color_bar = matrix_full[3]
        grid = matrix_full[4]
        # sixth canvas is for displaying a grid around selected cell

        # rotate the row_header canvas so they appear vertical
        row_header.rotate(math.radians(-90))
        row_header.translate(-self.layout_offset, 0)

        with canvas.hold_canvas(matrix_full):
            self.cell_x = np.tile(np.linspace(self.layout_offset, self.size, self.num_rows),
                                  self.num_rows)  # x-coordinates of cells
            self.cell_y = np.repeat(np.linspace(self.layout_offset, self.size, self.num_rows),
                                    self.num_rows)  # y-coordinates of cells
            self.cell_size = self.cell_x[1] - self.cell_x[0]

            grid.stroke_rects(self.cell_x, self.cell_y, height=self.cell_size, width=self.cell_size)
            value = matrix[self.from_row: self.from_row + self.num_rows, self.from_col: self.from_col + self.num_rows]
            colors = self._generate_color(self.connectivity, value=value, matrix_name=matrix_name)
            matrix_view.fill_styled_rects(self.cell_x, self.cell_y, color=colors, height=self.cell_size,
                                          width=self.cell_size)

            x = 0
            y = np.linspace(self.layout_offset, self.size, self.num_rows)
            grid.stroke_rects(y, x, height=self.layout_offset, width=self.cell_size)  # grid for row headers
            grid.stroke_rects(x, y, height=self.cell_size, width=self.layout_offset)  # grid for column headers

            for i in range(self.num_rows):
                row_header.font = f"bold {self.cell_size}px px sans serif"
                row_header_text = f"{self.connectivity.region_labels[self.from_row + i]}"
                row_header.fill_text(row_header_text, x + 10, y[i] + self.cell_size, max_width=self.layout_offset * 0.9)

                column_header.font = f"bold {self.cell_size}px px sans serif"
                column_header_text = f"{self.connectivity.region_labels[self.from_col + i]}"
                column_header.fill_text(column_header_text, x + 10, y[i] + self.cell_size,
                                        max_width=self.layout_offset * 0.9)

            self.colorbar_x = self.size * 1.1
            gradient = grid.create_linear_gradient(self.colorbar_x, self.layout_offset, self.size * 1.2, self.size,
                                                   [(i / len(self.colors), self.colors[-i - 1]) for i in
                                                    range(len(self.colors))])  # color gradient for color-bar
            grid.fill_style = gradient
            grid.fill_rect(self.colorbar_x, self.layout_offset, 20, self.size - self.layout_offset)
            grid.fill_style = "black"

            for i in range(7):
                label_text = f"--{round(matrix.max() * (6 - i) / 6, 2)}"
                color_bar.fill_text(label_text, self.colorbar_x + 20,
                                    self.size * 0.8 / 6.1 * i + self.layout_offset + 5)  # labels for colorbar

        return matrix_full

    def _generate_color(self, connectivity, i=0, j=0, matrix_name=None, value=None):
        self.colors = ["#66797b", "#543146", "#5a1c5d", "#b468ab", "#6ade42", "#27913c", "#1c464a",
                       "#247663", "#38bcaa", "#a9e9ff", "#61cfff", "#37a5c1", "#e4e4e2", "#ff9f25",
                       "#fb5226"]

        color_scheme = mcolors.LinearSegmentedColormap.from_list('color_scheme', self.colors)
        matrix = getattr(connectivity, matrix_name)
        norm = mcolors.Normalize(vmin=0, vmax=matrix.max())

        if not isinstance(value, np.ndarray):
            if not value:
                value = matrix[int(self.from_row + i)][int(self.from_col + j)]

            color = color_scheme(norm(value))
            color = f"rgba({color[0] * 255:.0f}, {color[1] * 255:.0f}, {color[2] * 255:.0f}, {color[3]:.2f})"
            return color

        colors = color_scheme(norm(value))
        colors = colors[:, :, :3] * 255
        return colors

    def set_mouse_position(self, x, y):
        self.x_coord = x
        self.y_coord = y

    def on_cell_clicked(self, x, y, matrix_name):
        self.clicked_matrix = matrix_name
        x_coord, y_coord = self.x_coord, self.y_coord
        col = ((x_coord - self.layout_offset) // self.cell_size)
        row = ((y_coord - self.layout_offset) // self.cell_size)

        if -1 < row < self.num_rows and -1 < col < self.num_rows:
            self.row = row
            self.col = col
            matrix = getattr(self.new_connectivity, matrix_name)
            value = matrix[int(self.from_row + self.row)][int(self.from_col + self.col)]
            matrix_ = self.clicked_matrix + "_matrix"
            matrix_ui = getattr(self, matrix_)

            x = self.layout_offset + self.col * self.cell_size
            y = self.layout_offset + self.row * self.cell_size
            self.popup_value.value = f"{value}"
            self.popup_error.value = ""
            self.popup.layout.visibility = 'visible'

            mid_col = self.num_rows // 2
            mid_row = self.num_rows // 2
            quadrant = 1  
            if self.col < mid_col and self.row < mid_row:
                quadrant = 1
            elif self.col >= mid_col and self.row < mid_row:
                quadrant = 2
            elif self.col < mid_col and self.row >= mid_row:
                quadrant = 3
            else:
                quadrant = 4

            if quadrant == 1:
                left = x - 1142
                top = y + self.cell_size + 2
            elif quadrant == 2:
                left = x - 1342 + self.cell_size
                top = y + self.cell_size + 2
            elif quadrant == 3:
                left = x - 1142
                top = y - 2
            else:
                left = x - 1342 + self.cell_size
                top = y - 2

            if quadrant in (3, 4):
                self.popup.add_class(POPUP_ABOVE_CLASS)
            else:
                self.popup.remove_class(POPUP_ABOVE_CLASS)
            self.popup.layout.left = f'{left}px'
            self.popup.layout.top = f'{top}px'
            self.current_matrix = matrix_name
            self.current_row = row
            self.current_col = col

            with canvas.hold_canvas(matrix_ui[5]):
                matrix_ui[5].clear()
                matrix_ui[5].line_width = 2
                matrix_ui[5].stroke_style = "white"
                matrix_ui[5].stroke_rect(x, y, self.cell_size, self.cell_size)

    def _show_popup_error(self, message):
        self.popup_error.value = format_message(message, ERROR_COLOR)
        LOGGER.warning(f"Matrix editor: '{self.popup_value.value}' is not a valid cell value.")
        self.popup_value.focus()

    def _read_cell_value(self):
        try:
            value = float(self.popup_value.value)
        except (ValueError, TypeError):
            self._show_popup_error(INVALID_NUMBER_MESSAGE)
            return None
        if not np.isfinite(value):
            self._show_popup_error(NOT_FINITE_MESSAGE)
            return None
        return max(value, 0.0)

    def on_apply_change(self, change):
        matrix_name = self.clicked_matrix + "_matrix"
        matrix_ui = getattr(self, matrix_name)
        value = self._read_cell_value()

        if value is not None:
            self.popup_error.value = ""
            matrix_name = self.clicked_matrix
            matrix = getattr(self.new_connectivity, matrix_name)
            max_val = matrix.max()
            matrix[self.from_row + int(self.row)][self.from_col + int(self.col)] = value
            if max_val != matrix.max():
                self._update_matrices_view(self.new_connectivity)

            self.popup.layout.visibility = "hidden"

            x = self.layout_offset + self.col * self.cell_size
            y = self.layout_offset + self.row * self.cell_size

            with canvas.hold_canvas(matrix_ui[0]):
                matrix_ui[0].fill_style = self._generate_color(self.new_connectivity, self.row, self.col,
                                                               self.clicked_matrix, value)
                matrix_ui[0].fill_rect(x, y, self.cell_size, self.cell_size)
                matrix_ui[0].stroke_rect(x, y, self.cell_size, self.cell_size)

            matrix_ui[5].clear()

    def on_click_cancel(self, change=None):
        self.popup.layout.visibility = "hidden"
        self.popup_error.value = ""

        matrix_name = self.clicked_matrix + "_matrix"
        matrix_ui = getattr(self, matrix_name)
        x = self.layout_offset + self.col * self.cell_size
        y = self.layout_offset + self.row * self.cell_size

        matrix = getattr(self.new_connectivity, self.clicked_matrix)
        value = matrix[self.from_row + int(self.row)][self.from_col + int(self.col)]

        # Redraw the cell with original color to remove highlight
        with canvas.hold_canvas(matrix_ui[0]):
            matrix_ui[0].fill_style = self._generate_color(self.new_connectivity, self.row, self.col,
                                                           self.clicked_matrix, value)
            matrix_ui[0].fill_rect(x, y, self.cell_size, self.cell_size)
            matrix_ui[0].stroke_rect(x, y, self.cell_size, self.cell_size)

        matrix_ui[5].clear()

    @property
    def conn_edited(self):
        return self._prepare_new_connectivity(source=self.new_connectivity)

    def _get_export_path(self, file_name):
        return os.path.join(os.getcwd(), file_name + H5_EXTENSION)

    def _get_next_free_name(self):
        index = 1
        while os.path.exists(self._get_export_path(f"{DEFAULT_EXPORT_NAME}_{index}")):
            index += 1
        return f"{DEFAULT_EXPORT_NAME}_{index}"

    def _show_export_message(self, message, color):
        self.export_message.value = format_message(message, color)

    def export_h5(self, connectivity):
        file_name = self.export_name.value.strip()
        if not is_valid_file_name(file_name):
            self._show_export_message(INVALID_FILE_NAME_MESSAGE, ERROR_COLOR)
            return None

        path = self._get_export_path(file_name)
        shown_name = file_name + H5_EXTENSION
        if os.path.exists(path):
            self._show_export_message(FILE_EXISTS_MESSAGE.format(shown_name), ERROR_COLOR)
            return None

        try:
            populate_datatypes_registry()
            h5.store(connectivity, path)
        except (OSError, TVBException):
            LOGGER.exception(f"Matrix editor: could not export the connectivity to {path}.")
            self._show_export_message(EXPORT_FAILED_MESSAGE.format(shown_name), ERROR_COLOR)
            return None

        self._show_export_message(EXPORT_SUCCESS_MESSAGE.format(shown_name), SUCCESS_COLOR)
        self.export_name.value = self._get_next_free_name()
        return path

    def _on_click_export(self, button):
        self.export_h5(self.conn_edited)

    def _prepare_new_connectivity(self, source=None):
        if source is None:
            source = self.connectivity
        new_connectivity = Connectivity()
        new_connectivity.parent_connectivity = self.connectivity.gid.hex
        new_connectivity.centres = source.centres
        new_connectivity.region_labels = source.region_labels
        new_connectivity.orientations = source.orientations
        new_connectivity.cortical = source.cortical
        new_connectivity.hemispheres = source.hemispheres
        new_connectivity.areas = source.areas
        new_connectivity.weights = source.weights
        new_connectivity.tract_lengths = source.tract_lengths
        new_connectivity.configure()

        return new_connectivity

    def _update_matrices_view(self, connectivity):
        matrices = ["weights", "tract_lengths"]
        for matrix_name in matrices:
            matrix_view = getattr(self, matrix_name + "_matrix")
            matrix = getattr(connectivity, matrix_name)

            with canvas.hold_canvas(matrix_view):
                matrix_view[0].clear()
                matrix_view[1].clear()
                matrix_view[2].clear()
                matrix_view[3].clear()
                matrix_view[5].clear()

                value = matrix[self.from_row: self.from_row + self.num_rows,
                        self.from_col: self.from_col + self.num_rows]
                color = self._generate_color(connectivity, value=value, matrix_name=matrix_name)
                matrix_view[0].fill_styled_rects(self.cell_x, self.cell_y, color=color, height=self.cell_size,
                                                 width=self.cell_size)

                max_value = matrix.max()
                region_labels = self.connectivity.region_labels

                x = 0
                y = np.linspace(self.layout_offset, self.size, self.num_rows)
                for i in range(self.num_rows):
                    row_label = region_labels[self.from_row + i]
                    matrix_view[1].fill_text(row_label, x + 10, y[i] + self.cell_size,
                                             max_width=self.layout_offset * 0.9)

                for i in range(self.num_rows):
                    col_label = region_labels[self.from_col + i]
                    matrix_view[2].fill_text(col_label, x + 10, y[i] + self.cell_size,
                                             max_width=self.layout_offset * 0.9)

                for i in range(7):
                    value = f"--{round(max_value * (6 - i) / 6, 2)}"
                    matrix_view[3].fill_text(value, self.colorbar_x + 20, ((self.size - self.layout_offset) / 6.1) * i +
                                             self.layout_offset + 5)  # labels for colorbar

    def display(self):
        display(self.header)
        display(self.tab)

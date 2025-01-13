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
import ipycanvas as canvas
import ipywidgets as widgets
import matplotlib.colors as mcolors
from IPython.display import display
from tvb.datatypes.connectivity import Connectivity

from tvbwidgets import get_logger
from tvbwidgets.ui.base_widget import TVBWidget

LOGGER = get_logger(__name__)


class ConnectivityMatrixEditor(TVBWidget):
    def __init__(self, connectivity, size=None, **kwargs):
        super().__init__(**kwargs)
        self.connectivity = connectivity
        self.connectivity_history_list = [self.connectivity]
        self.num_rows = int(len(self.connectivity.weights[0]) / 2)  # num_cols will be equal to num_rows
        if size is None:
            size = self.num_rows * 20
        self.size = size
        self.layout_offset = self.size * 0.2

        self.is_connectivity_being_edited = True
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

        self.cell_value = widgets.Text(description="value",
                                       layout=widgets.Layout(width="200px", visibility="hidden"))

        self.change_button = widgets.Button(description="Change",
                                            layout=widgets.Layout(width="80px", visibility="hidden"))
        self.change_button.on_click(self.on_apply_change)

        self.save_button = widgets.Button(description="Save",
                                          layout=widgets.Layout(width="100px", margin='0 0 0 auto'))
        self.save_button.on_click(self.on_click_save)

        self.header.children = [self.quadrants, self.cell_value, self.change_button, self.save_button,
                                self._get_history_dropdown()]

    def _on_quadrant_select(self, change):
        self.cell_value.layout.visibility = "hidden"
        self.change_button.layout.visibility = "hidden"

        selection = int(change["new"][-1])
        connectivity = self.new_connectivity if self.is_connectivity_being_edited else self.connectivity

        self._get_quadrant_range(selection)
        self._update_matrices_view(connectivity)

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

    def _prepare_matrices_tab(self):
        self.weights_matrix = self._prepare_matrix("weights")
        self.tract_lengths_matrix = self._prepare_matrix("tract_lengths")

        self.weights_matrix.on_mouse_down(lambda x, y: self.on_cell_clicked(x, y, "weights"))
        self.weights_matrix.on_mouse_move(self.set_mouse_position)

        self.tract_lengths_matrix.on_mouse_down(lambda x, y: self.on_cell_clicked(x, y, "tract_lengths"))
        self.tract_lengths_matrix.on_mouse_move(self.set_mouse_position)

        out1 = widgets.Output()
        out2 = widgets.Output()

        with out1:
            display(self.weights_matrix)

        with out2:
            display(self.tract_lengths_matrix)

        container1 = widgets.Box([out1], layout=widgets.Layout(
            width='1200px',
            height='600px',
            overflow_x='auto',
            overflow_y='auto',
        ))

        container2 = widgets.Box([out2], layout=container1.layout)

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
            connectivity = self.new_connectivity if self.is_connectivity_being_edited else self.connectivity
            matrix = getattr(connectivity, matrix_name)
            value = matrix[int(self.from_row + self.row)][int(self.from_col + self.col)]
            self.cell_value.value = f"{value}"

            self.cell_value.layout.visibility = "visible"
            self.change_button.layout.visibility = "visible"

            matrix_ = self.clicked_matrix + "_matrix"
            matrix_ui = getattr(self, matrix_)

            x = self.layout_offset + self.col * self.cell_size
            y = self.layout_offset + self.row * self.cell_size

            with canvas.hold_canvas(matrix_ui[5]):
                matrix_ui[5].clear()
                matrix_ui[5].line_width = 2
                matrix_ui[5].stroke_style = "white"
                matrix_ui[5].stroke_rect(x, y, self.cell_size, self.cell_size)

    def on_apply_change(self, change):
        self.is_connectivity_being_edited = True

        matrix_name = self.clicked_matrix + "_matrix"
        matrix_ui = getattr(self, matrix_name)
        try:
            value = float(self.cell_value.value)
        except (ValueError, TypeError):
            LOGGER.error(f'An exception occurred when retrieving the cell value.')
            value = None

        if value is not None:
            matrix_name = self.clicked_matrix
            matrix = getattr(self.new_connectivity, matrix_name)
            max_val = matrix.max()
            matrix[self.from_row + int(self.row)][self.from_col + int(self.col)] = value
            if max_val != matrix.max():
                self._update_matrices_view(self.new_connectivity)

            self.cell_value.layout.visibility = "hidden"
            self.change_button.layout.visibility = "hidden"

            x = self.layout_offset + self.col * self.cell_size
            y = self.layout_offset + self.row * self.cell_size

            with canvas.hold_canvas(matrix_ui[0]):
                matrix_ui[0].fill_style = self._generate_color(self.new_connectivity, self.row, self.col,
                                                               self.clicked_matrix, value)
                matrix_ui[0].fill_rect(x, y, self.cell_size, self.cell_size)
                matrix_ui[0].stroke_rect(x, y, self.cell_size, self.cell_size)

            matrix_ui[5].clear()

    def saved_connectivities(self):
        conn_list = []
        for conn in self.connectivity_history_list:
            conn_list.append(conn.gid.hex)
        return conn_list

    def get_connectivity(self, gid=None):
        if gid is None:
            return self.connectivity
        for conn in self.connectivity_history_list:
            if conn.gid.hex == gid:
                return conn

    def on_click_save(self, change):
        self.cell_value.layout.visibility = "hidden"
        self.change_button.layout.visibility = "hidden"

        conn = self.new_connectivity
        self.connectivity_history_list.insert(0, conn)
        self.connectivity = conn
        self.header.children = list(self.header.children)[:-1] + [self._get_history_dropdown()]

        self.new_connectivity = self._prepare_new_connectivity()
        self.is_connectivity_being_edited = False
        self._update_matrices_view(self.connectivity)

    def _prepare_new_connectivity(self):
        new_connectivity = Connectivity()
        new_connectivity.parent_connectivity = self.connectivity.gid.hex
        new_connectivity.centres = self.connectivity.centres
        new_connectivity.region_labels = self.connectivity.region_labels
        new_connectivity.orientations = self.connectivity.orientations
        new_connectivity.cortical = self.connectivity.cortical
        new_connectivity.hemispheres = self.connectivity.hemispheres
        new_connectivity.areas = self.connectivity.areas
        new_connectivity.weights = self.connectivity.weights
        new_connectivity.tract_lengths = self.connectivity.tract_lengths
        new_connectivity.configure()

        return new_connectivity

    def _get_history_dropdown(self):
        values = [(conn.gid.hex, conn) for conn in self.connectivity_history_list]
        default = values[values.index((self.connectivity.gid.hex, self.connectivity))][1]

        dropdown = widgets.Dropdown(options=values,
                                    description='View history',
                                    disabled=False,
                                    value=default,
                                    )

        def on_connectivity_change(change):
            self.cell_value.layout.visibility = "hidden"
            self.change_button.layout.visibility = "hidden"

            self.is_connectivity_being_edited = False
            self.connectivity = change["new"]
            self.new_connectivity = self._prepare_new_connectivity()
            self._update_matrices_view(self.connectivity)

        dropdown.observe(on_connectivity_change, 'value')
        return dropdown

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

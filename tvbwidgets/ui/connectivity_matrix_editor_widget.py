# -*- coding: utf-8 -*-
#
# "TheVirtualBrain - Widgets" package
#
# (c) 2022-2024, TVB Widgets Team
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
from tvbwidgets.ui.base_widget import TVBWidget

class ConnectivityMatrixEditor(TVBWidget):
    def __init__(self, connectivity, size = 600):
        self.size = size
        self.connectivity = connectivity
        self.weights = self.connectivity.weights
        self.tract_lengths = self.connectivity.tract_lengths
        self.connectivities_history = [self.connectivity]
        self.num_rows = int(len(self.connectivity.weights[0])/2)
        self.num_cols = int(len(self.connectivity.weights[1])/2)  
        self.cell_size = self.size / (self.num_rows + 5)
        
        self.new_connectivity = self._prepare_new_connectivity()
        self.is_matrix_saved = False
        self.header = widgets.HBox(layout = self.DEFAULT_BORDER)
        self._make_header()
        self.tab = widgets.Tab(layout = self.DEFAULT_BORDER)
        self._get_quadrant_range(selection = 1)
        self._prepare_matrices_tab()
        
    def _make_header(self):
        options = ["Quadrant 1", "Quadrant 2", "Quadrant 3", "Quadrant 4"]
        
        self.quadrants = widgets.Dropdown(options = options)
        self.quadrants.observe(self._on_quadrant_select, names = ["value"])
        
        self.cell_value = widgets.Text(description = "value", 
                                      layout = widgets.Layout(width = "200px", visibility = "hidden"))
        
        self.change_button = widgets.Button(description = "Change",
                                    layout = widgets.Layout(width = "80px", visibility = "hidden"))
        self.change_button.on_click(lambda change :self.on_apply_change(change))

        self.save_button = widgets.Button(description = "Save", 
                                         layout = widgets.Layout(width = "100px", margin='0 0 0 auto'))
        self.save_button.on_click(self.on_click_save)

        self.header.children = [self.quadrants, self.cell_value, self.change_button, self.save_button, self._get_history_dropdown()]

    def _on_quadrant_select(self, change):
        self.cell_value.layout.visibility = "hidden"
        self.change_button.layout.visibility = "hidden"
    
        connectivity = self.connectivity if self.is_matrix_saved else self.new_connectivity
        selection = int(change["new"][-1])
        self._get_quadrant_range(selection)
        self._update_matrices_view(connectivity)



    def _get_quadrant_range(self, selection):
        if selection == 1:
            from_row = 0
            from_col = 0
        elif selection == 2:
            from_row = int(self.weights.shape[0]/2)
            from_col = 0
        elif selection == 3:
            from_row = 0
            from_col = int(self.weights.shape[0]/2)
        else:
            from_row = int(self.weights.shape[0]/2)
            from_col = int(self.weights.shape[0]/2)

        self.from_row = from_row
        self.from_col = from_col

    def _prepare_matrices_tab(self):
        self.weights_matrix = self._prepare_matrix("weights")
        self.tract_lengths_matrix =  self._prepare_matrix("tract_lengths")

        self.weights_matrix.on_mouse_down(lambda x, y: self.on_cell_clicked(x, y, "weights"))
        self.weights_matrix.on_mouse_move(self.set_mouse_position)
        
        self.tract_lengths_matrix.on_mouse_down(lambda x, y: self.on_cell_clicked(x, y, "tract_lengths"))
        self.tract_lengths_matrix.on_mouse_move(self.set_mouse_position)
        
        self.tab.children = [self.weights_matrix, self.tract_lengths_matrix]
        self.tab.set_title(0, "weights")
        self.tab.set_title(1, "tract_lengths")

    def _prepare_matrix(self, matrix_name):
        cell_size = self.cell_size
        matrix = getattr(self.connectivity, matrix_name)
        matrix_full = canvas.MultiCanvas(5, width=self.size + 10*cell_size, height=self.size + 10*cell_size)

        matrix_view = matrix_full[0]
        row_header = matrix_full[1]
        column_header = matrix_full[2]
        color_bar = matrix_full[3]
        grid = matrix_full[4]

        #rotate the row_header canvas so they appear vertical
        row_header.rotate(math.radians(-90))
        row_header.translate(-cell_size * 10 ,0)

        with canvas.hold_canvas(matrix_full):
            x= np.tile(np.linspace(cell_size * 8, cell_size * 45, self.num_cols), self.num_cols)   #x-coordinates of cells
            y= np.repeat(np.linspace(cell_size * 7, cell_size * 44, self.num_rows), self.num_rows)   #y-coordinates of cells
            grid.stroke_rects(x, y, height = cell_size, width = cell_size)
            colors = self._generate_color(self.connectivity, value=matrix[self.from_row : self.from_row + self.num_rows, self.from_col : self.from_col + self.num_cols],  matrix_name=matrix_name)
            matrix_view.fill_styled_rects(x, y, color = colors, height = cell_size - 1, width = cell_size -1)

            for i in range(self.num_rows):
                grid.stroke_rect(cell_size * 3, (i + 7) * cell_size, cell_size * 5, cell_size)   #grid for row headers
                grid.stroke_rect( (i + 8) * cell_size, cell_size * 2, cell_size, cell_size * 5)  #grid for column headers
                row_header.font = f"bold {self.cell_size * 0.90}px px sans serif"
                row_header.fill_text(f"{self.connectivity.region_labels[self.from_row + i]}", cell_size * 3.5, (i + 9) * cell_size, max_width = cell_size * 5)
                column_header.font = f"bold {self.cell_size * 0.90}px px sans serif"
                column_header.fill_text(f"{self.connectivity.region_labels[self.from_col + i]}", cell_size * 3.5, (i + 8) * cell_size, max_width = cell_size * 5)

            gradient = grid.create_linear_gradient(cell_size * 47, cell_size * 7.5, cell_size * 47 , cell_size * 35,
                            [(i/len(self.colors),self.colors[-i-1]) for i in range(len(self.colors))])   #color gradient for color-bar
            grid.fill_style = gradient
            grid.fill_rect(cell_size * 47, cell_size * 7.5, cell_size , cell_size * 25)
            grid.fill_style = "black"

            for i in range(7):
                color_bar.fill_text(f"-{round(int(matrix.max()) * (6 - i) / 6, 2)}", cell_size * 48, i * cell_size * 4 + cell_size * 8)   #labels for colorbar
        
        return matrix_full

    def _generate_color(self, connectivity, i=0, j=0, matrix_name=None , value = None):
        self.colors = ["#66797b", "#543146", "#5a1c5d", "#b468ab", "#6ade42", "#27913c", "#1c464a", 
          "#247663", "#38bcaa", "#a9e9ff", "#61cfff", "#37a5c1", "#e4e4e2", "#ff9f25", 
          "#fb5226"]

        color_scheme = mcolors.LinearSegmentedColormap.from_list('color_scheme', self.colors)
        matrix = getattr(connectivity, matrix_name)
        norm = mcolors.Normalize(vmin=0, vmax=matrix.max())

        if not isinstance(value, np.ndarray):
            if  not value:
                value = matrix[int(self.from_row + i)][int(self.from_col + j)]

            color = color_scheme(norm(value))
            color = f"rgba({color[0]*255:.0f}, {color[1]*255:.0f}, {color[2]*255:.0f}, {color[3]:.2f})"
            return color
        
        colors = color_scheme(norm(value))
        colors = colors[:, :, :3] * 255
        return colors
    
    def set_mouse_position(self, x, y):
        self.x_coord = x
        self.y_coord = y
            
    def on_cell_clicked(self, x, y, matrix_name):
        self.clicked_matrix = matrix_name
        x_coord, y_coord  = self.x_coord , self.y_coord
        col = (x_coord // self.cell_size) - 8
        row = (y_coord // self.cell_size) - 7

        if row > -1 and row < self.num_rows and col > -1 and col < self.num_cols:
            self.row = row
            self.col = col
            connectivity = self.connectivity if self.is_matrix_saved else self.new_connectivity
            matrix = getattr(connectivity, matrix_name)
            value = matrix[int(self.from_row + self.row)][int(self.from_col + self.col)]
            self.cell_value.value = f"{value}"

            self.cell_value.layout.visibility = "visible"
            self.change_button.layout.visibility = "visible"
        
    def on_apply_change(self, change):
        if self.is_matrix_saved == True:
            self.is_matrix_saved = False
        matrix_name = self.clicked_matrix + "_matrix"
        matrix_ui = getattr(self, matrix_name)
        value = float(self.cell_value.value)

        matrix_name =  self.clicked_matrix
        matrix = getattr(self.new_connectivity, matrix_name)
        max_val = matrix.max()
        matrix[self.from_row + int(self.row)][self.from_col + int(self.col)] = value
        if max_val != matrix.max():
            self._update_matrices_view(self.new_connectivity)
        

        self.cell_value.layout.visibility = "hidden"
        self.change_button.layout.visibility = "hidden"

        with canvas.hold_canvas(matrix_ui[0]):
            matrix_ui[0].fill_style = self._generate_color(self.new_connectivity, self.row, self.col, self.clicked_matrix, value)
            matrix_ui[0].fill_rect((self.col + 8) * self.cell_size, (self.row + 7) * self.cell_size, self.cell_size, self.cell_size)
            matrix_ui[0].stroke_rect((self.col + 8) * self.cell_size, (self.row + 7) * self.cell_size, self.cell_size, self.cell_size)

    def get_connectivity(self, gid=None):
        if gid is None:
            return self.connectivity
        for conn in self.connectivities_history:
            if conn.gid.hex == gid.hex:
                return conn

    def on_click_save(self, change):
        self.cell_value.layout.visibility = "hidden"
        self.change_button.layout.visibility = "hidden"

        conn = self.new_connectivity
        self.connectivities_history.insert(0, conn)
        self.header.children = list(self.header.children)[:-1] + [self._get_history_dropdown()]
        self.new_connectivity = self._prepare_new_connectivity()
        self.is_matrix_saved = True
        self._update_matrices_view(self.connectivity)
        

    def _prepare_new_connectivity(self):
        self.new_connectivity = Connectivity()
        self.new_connectivity.parent_connectivity = self.connectivity.gid.hex
        self.new_connectivity.centres = self.connectivity.centres
        self.new_connectivity.region_labels = self.connectivity.region_labels
        self.new_connectivity.orientations = self.connectivity.orientations
        self.new_connectivity.cortical = self.connectivity.cortical
        self.new_connectivity.hemispheres = self.connectivity.hemispheres
        self.new_connectivity.areas = self.connectivity.areas
        self.new_connectivity.weights = self.connectivity.weights
        self.new_connectivity.tract_lengths = self.connectivity.tract_lengths
        self.new_connectivity.configure()
  
        return self.new_connectivity
        
    def _get_history_dropdown(self):
        values = [(conn.gid.hex, conn) for conn in self.connectivities_history]
        default = len(values) and values[-1][1] or None

        dropdown = widgets.Dropdown(options=values,
                                       description='View history',
                                       disabled=False,
                                       value=default,
                                       )

        def on_connectivity_change(change):
            self.cell_value.layout.visibility = "hidden"
            self.change_button.layout.visibility = "hidden"

            self.is_matrix_saved = True
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
            matrix_view[0].clear()
            matrix_view[1].clear()
            matrix_view[2].clear()
            matrix_view[3].clear()

            x= np.tile(np.linspace(self.cell_size * 8, self.cell_size * 45, self.num_cols), self.num_cols)
            y= np.repeat(np.linspace(self.cell_size * 7, self.cell_size * 44, self.num_rows), self.num_rows)
            value = matrix[self.from_row:self.from_row + self.num_rows, self.from_col:self.from_col + self.num_cols]
            matrix_view[0].fill_styled_rects(x, y, color = self._generate_color(connectivity, value=value, matrix_name=matrix_name), height = self.cell_size - 1, width = self.cell_size - 1)
            
            max_value = int(matrix.max())
            region_labels = self.connectivity.region_labels
            
            for i in range(self.num_rows):
                row_label = region_labels[self.from_row + i]
                matrix_view[1].fill_text(row_label, self.cell_size * 3.5, (i + 9) * self.cell_size, max_width = self.cell_size * 5)
                
            for i in range(self.num_cols):
                col_label = region_labels[self.from_col + i]
                matrix_view[2].fill_text(col_label, self.cell_size * 3.5, (i + 8) * self.cell_size, max_width = self.cell_size * 5)

            for i in range(7):
                value = f"-{round(max_value * (6 - i) / 6, 2)}"
                matrix_view[3].fill_text(value, self.cell_size * 48, i * self.cell_size * 4 + self.cell_size * 8)

    def display(self):
        display(self.header)
        display(self.tab)  
import math
import numpy as np
import ipycanvas as canvas
import ipywidgets as widgets
import matplotlib.colors as mcolors
from IPython.display import display
from tvb.datatypes.connectivity import Connectivity

class ConnectivityMatrixEditor():
    def __init__(self, connectivity):
        self.connectivity = connectivity
        self.weights = self.connectivity.weights
        self.tract_lengths = self.connectivity.tract_lengths
        self.connectivities_history = [self.connectivity]
        self.cell_size = 20
        self.num_rows = int(len(self.connectivity.weights[0])/2)
        self.num_cols = int(len(self.connectivity.weights[1])/2)  
        self._make_header()
        self.tab = widgets.Tab()
        self._get_quadrant_range(selection = 1)
        self._prepare_matrices_tab()
        self.new_connectivity = self._prepare_new_connectivity()


    def _make_header(self):
        self.header = widgets.HBox()
        options = ["Quadrant 1", "Quadrant 2", "Quadrant 3", "Quadrant 4"]
        self.quadrants = widgets.Dropdown(options = options)
        self.quadrants.observe(self._on_quadrant_select, names = ["value"])
        self.cell_value = widgets.Text(description = "value")
        self.button = widgets.Button(description = "Change")
        self.button.on_click(lambda change :self.on_apply_change(change))
        self.cell_value.layout.visibility = "hidden"
        self.button.layout.visibility = "hidden"
        self.cell_value.layout.width = "200px"
        self.button.layout.width ="80px"
        self.save_button = widgets.Button(description = "Save", layout = widgets.Layout(margin='0 0 0 auto'))
        self.save_button.on_click(self.on_click_save)
        self.save_button.layout.width ="100px"
        self.header.children = [self.quadrants, self.cell_value, self.button, self.save_button, self._get_history_dropdown()]

    def _on_quadrant_select(self, change):
        selection = int(change["new"][-1])
        self._get_quadrant_range(selection)
        self._update_matrices_view()

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
        self.tract_lengths_matrix.on_mouse_down(lambda x, y: self.on_cell_clicked(x, y, "tract_lengths"))
        self.tab.children = [self.weights_matrix, self.tract_lengths_matrix]
        self.tab.set_title(0, "weights")
        self.tab.set_title(1, "tract_lengths")

    def _prepare_matrix(self, matrix_name):
        cell_size = self.cell_size
        matrix = getattr(self.connectivity, matrix_name)
        matrix_full = canvas.MultiCanvas(5, width=1200, height= 1200)

        matrix_view = matrix_full[0]
        row_header = matrix_full[1]
        column_header = matrix_full[2]
        color_bar = matrix_full[3]
        grid = matrix_full[4]

        row_header.rotate(math.radians(-90))
        row_header.translate(-200 ,0)

        with canvas.hold_canvas(matrix_full):
            x= np.tile(np.linspace(160, 900, self.num_cols), self.num_cols)
            y= np.repeat(np.linspace(140, 881, self.num_rows), self.num_rows)
            grid.stroke_rects(x, y, height = cell_size, width = cell_size)
            matrix_view.fill_styled_rects(x, y, color = self._generate_color(value=matrix[self.from_row : self.from_row + 38, self.from_col : self.from_col + 38], matrix_name=matrix_name), height = cell_size - 1, width = cell_size -1)

            for i in range(self.num_rows):
                grid.stroke_rect( (i + 8) * cell_size, 60, cell_size, 100)
                grid.stroke_rect(60, (i + 7) * cell_size, 100, cell_size)
                column_header.font = "15px px sans serif"
                column_header.fill_text(f"{self.connectivity.region_labels[self.from_col + i]}", 70, (i + 8) * cell_size, max_width = 100)
                row_header.font = "15px px sans serif"
                row_header.fill_text(f"{self.connectivity.region_labels[self.from_row + i]}", 70, (i + 9) * cell_size, max_width = 100)

            gradient = grid.create_linear_gradient(1000, 150, 1000, 700,
                            [(i/len(self.colors),self.colors[i]) for i in range(len(self.colors))])
            grid.fill_style = gradient
            grid.fill_rect(1000, 150, 30, 500)
            grid.fill_style = "black"
            for i in range(7):
                color_bar.fill_text(f"-{int(matrix.max()) * i / 6}", 1030, i * 80 + 160)
        
        return matrix_full

    def _generate_color(self, i=0, j=0, matrix_name=None , value = None):
        self.colors = ["#66797b", "#543146", "#5a1c5d", "#b468ab", "#6ade42", "#27913c", "#1c464a", 
          "#247663", "#38bcaa", "#a9e9ff", "#61cfff", "#37a5c1", "#e4e4e2", "#ff9f25", 
          "#fb5226"]

        color_scheme = mcolors.LinearSegmentedColormap.from_list('color_scheme', self.colors)
        matrix = getattr(self.connectivity, matrix_name)
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
            
    def on_cell_clicked(self, x, y, matrix_name):
        self.clicked_matrix = matrix_name
        col = (x // self.cell_size) - 8
        row = (y // self.cell_size) - 7
        if row > -1 and row < self.num_rows and col > -1 and col < self.num_cols:
            self.row = row
            self.col = col
            matrix = getattr(self.connectivity, matrix_name)
            value = matrix[int(self.from_row + self.row)][int(self.from_col + self.col)]
            self.cell_value.value = f"{value}"
            self.cell_value.layout.visibility = "visible"
            self.button.layout.visibility = "visible"
        
    def on_apply_change(self, change):
        matrix_name = self.clicked_matrix + "_matrix"
        matrix_ui = getattr(self, matrix_name)
        self.cell_value.layout.visibility = "hidden"
        self.button.layout.visibility = "hidden"
        with canvas.hold_canvas(matrix_ui[0]):
            matrix_ui[0].fill_style = self._generate_color(self.row, self.col, self.clicked_matrix, float(self.cell_value.value))
            matrix_ui[0].fill_rect((self.col + 8) * self.cell_size, (self.row + 7) * self.cell_size, self.cell_size, self.cell_size)
            matrix_ui[0].stroke_rect((self.col + 8) * self.cell_size, (self.row + 7) * self.cell_size, self.cell_size, self.cell_size)
        matrix_name =  self.clicked_matrix
        matrix = getattr(self.new_connectivity, matrix_name)
        matrix[int(self.row)][int(self.col)] = float(self.cell_value.value)

    def get_connectivity(self, gid=None):
        if gid is None:
            return self.connectivity
        for conn in self.connectivities_history:
            if conn.gid.hex == gid.hex:
                return conn

    def on_click_save(self, change):
        conn = self.new_connectivity
        self.connectivities_history.append(conn)
        self.connectivity = self.new_connectivity
        self.header.children = list(self.header.children)[:-1] + [self._get_history_dropdown()]
        self.new_connectivity = self._prepare_new_connectivity()
        self._get_quadrant_range(selection=1)
        self._update_matrices_view()

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
            self.connectivity = change["new"]
            self._get_quadrant_range(selection=1)
            self._update_matrices_view()

        dropdown.observe(on_connectivity_change, 'value')
        return dropdown
    
    def _update_matrices_view(self):
        matrices = ["weights", "tract_lengths"]
        for matrix_name in matrices:
            matrix_view = getattr(self, matrix_name + "_matrix")
            matrix = getattr(self.connectivity, matrix_name)
            matrix_view[0].clear()
            matrix_view[1].clear()
            matrix_view[2].clear()
            matrix_view[3].clear()
            x = np.tile(np.linspace(160, 900, self.num_cols), self.num_cols)
            y = np.repeat(np.linspace(140, 881, self.num_rows), self.num_rows)
            value = matrix[self.from_row:self.from_row + self.num_rows,self.from_col:self.from_col + self.num_cols]
            matrix_view[0].fill_styled_rects(x, y, color = self._generate_color(value=value, matrix_name=matrix_name), height = self.cell_size - 1, width = self.cell_size - 1)
            max_value = int(matrix.max())
            region_labels = self.connectivity.region_labels
            for i in range(self.num_rows):
                row_label = region_labels[self.from_row + i]
                matrix_view[1].fill_text(row_label, 70, (i + 9) * self.cell_size, max_width=100)
                
            for i in range(self.num_cols):
                col_label = region_labels[self.from_col + i]
                matrix_view[2].fill_text(col_label, 70, (i + 8) * self.cell_size, max_width=100)

            for i in range(7):
                value = f"-{max_value * i / 6}"
                matrix_view[3].fill_text(value, 1030, i * 80 + 160)

    def display(self):
        display(self.header)
        display(self.tab)
      
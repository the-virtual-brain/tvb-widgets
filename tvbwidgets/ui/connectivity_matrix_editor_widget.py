import math
import ipycanvas as canvas
import ipywidgets as widgets
import matplotlib.colors as mcolors
from IPython.display import display

class ConnectivityMatrixEditor():
    def __init__(self, connectivity):
        self.connectivity = connectivity
        self.weights = self.connectivity.weights
        self.tract_lengths = self.connectivity.tract_lengths
        self.cell_size = 20
        self.num_rows = int(len(self.connectivity.weights[0])/2)
        self.num_cols = int(len(self.connectivity.weights[1])/2)  
        self._make_header()
        self.tab = widgets.Tab()
        self._get_quadrant_range(selection = 1)
        self._prepare_matrices_tab()

    def _make_header(self):
        options = ["Quadrant 1", "Quadrant 2", "Quadrant 3", "Quadrant 4"]
        self.quadrants = widgets.Dropdown(options = options)
        self.quadrants.observe(self._on_quadrant_select, names = ["value"])
        self.header = widgets.HBox()
        self.cell_value = widgets.Text(description = "value")
        self.button = widgets.Button(description = "Change")
        self.button.on_click(lambda change :self.on_apply_change(change))
        self.cell_value.layout.visibility = "hidden"
        self.button.layout.visibility = "hidden"
        self.cell_value.layout.width = "200px"
        self.button.layout.width ="80px"
        self.header.children = [self.quadrants, self.cell_value, self.button]

    def _on_quadrant_select(self, change):
        selection = int(change["new"][-1])
        self.weights_matrix.clear()
        self.tract_lengths_matrix.clear()
        self._get_quadrant_range(selection)
        self._prepare_matrices_tab()

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
        rows = self.num_rows
        cols = self.num_cols
        matrix_full = canvas.MultiCanvas(4, width=1200, height= 1200)

        matrix = matrix_full[0]
        row_header = matrix_full[1]
        column_header = matrix_full[2]
        color_bar = matrix_full[3]

        row_header.rotate(math.radians(-90))
        row_header.translate(-200 ,0)
        with canvas.hold_canvas(matrix_full):
            for i in range(rows):
                column_header.font = "15px px sans serif"
                column_header.stroke_rect(60, (i + 7) * 20, 100, 20)
                column_header.fill_text(f"{self.connectivity.region_labels[self.from_col + i]}", 70, (i + 8) * 20, max_width = 100)
                row_header.font = "15px px sans serif"
                row_header.stroke_rect(60, (i + 8) * 20, 100, 20)
                row_header.fill_text(f"{self.connectivity.region_labels[self.from_row + i]}", 70, (i + 9) * 20, max_width = 100)

                for j in range(cols):
                    matrix.fill_style = self._generate_color(i, j, matrix_name)
                    matrix.fill_rect((j + 8) * cell_size, (i + 7) * cell_size, cell_size, cell_size)
                    matrix.stroke_rect((j + 8) * cell_size, (i + 7) * cell_size, cell_size, cell_size)
                    matrix.stroke_style = "black"
                    matrix.line_width = 2

            gradient = color_bar.create_linear_gradient(1000, 150, 1000, 700,
                            [(i/len(self.colors),self.colors[i]) for i in range(len(self.colors))])
            color_bar.fill_style = gradient
            color_bar.fill_rect(1000, 150, 30, 500)
            color_bar.fill_style = "black"
            matrix_name = getattr(self, matrix_name)
            for i in range(7):
                color_bar.fill_text(f"-{int(matrix_name.max()) * i / 6}", 1030, i * 80 + 160)
        
        return matrix_full

    def _generate_color(self, i, j, matrix_name , value = None):
        self.colors = ["#66797b", "#543146", "#5a1c5d", "#b468ab", "#6ade42", "#27913c", "#1c464a", 
          "#247663", "#38bcaa", "#a9e9ff", "#61cfff", "#37a5c1", "#e4e4e2", "#ff9f25", 
          "#fb5226"]

        color_scheme = mcolors.LinearSegmentedColormap.from_list('color_scheme', self.colors)
        matrix = getattr(self, matrix_name)
        norm = mcolors.Normalize(vmin=0, vmax=matrix.max())
        if not value:
            value = matrix[int(self.from_row + i)][int(self.from_col + j)]
        color = color_scheme(norm(value))
        color = f"rgba({color[0]*255:.0f}, {color[1]*255:.0f}, {color[2]*255:.0f}, {color[3]:.2f})"
        return color
    
    def on_cell_clicked(self, x, y, matrix_name):
        self.clicked_matrix = matrix_name
        col = (x // self.cell_size) - 8
        row = (y // self.cell_size) - 7
        if row > -1 and row < self.num_rows and col > -1 and col < self.num_cols:
            self.row = row
            self.col = col
            matrix = getattr(self, matrix_name)
            value = matrix[int(self.from_row + self.row)][int(self.from_col + self.col)]
            self.cell_value.value = f"{value}"
            self.cell_value.layout.visibility = "visible"
            self.button.layout.visibility = "visible"
        
    def on_apply_change(self, change):
        matrix_name = self.clicked_matrix + "_matrix"
        matrix = getattr(self, matrix_name)
        self.cell_value.layout.visibility = "hidden"
        self.button.layout.visibility = "hidden"
        with canvas.hold_canvas(matrix[0]):
            matrix[0].fill_style = self._generate_color(self.row, self.col, self.clicked_matrix, float(self.cell_value.value))
            matrix[0].fill_rect((self.col + 8) * self.cell_size, (self.row + 7) * self.cell_size, self.cell_size, self.cell_size)
            matrix[0].stroke_rect((self.col + 8) * self.cell_size, (self.row + 7) * self.cell_size, self.cell_size, self.cell_size)
        
    def display(self):
        display(self.header)
        display(self.tab)
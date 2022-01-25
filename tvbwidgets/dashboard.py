import ipywidgets
import tvb.simulator.integrators as integrators_module
import tvb.simulator.models as models_module
from IPython.core.display_functions import display

from tvbwidgets.drive_upload_widget import DriveUploadWidget
from tvbwidgets.phase_plane_widget import PhasePlaneWidget
from tvbwidgets.surface_viewer_widget import SurfaceViewer


class Dashboard(object):

    def __init__(self):
        pp_widget = PhasePlaneWidget(model=models_module.Generic2dOscillator(),
                                     integrator=integrators_module.HeunDeterministic()).get_widget()
        upload_widget = DriveUploadWidget().get_widget()
        view_widget = SurfaceViewer().get_widget()

        self.tab = ipywidgets.Tab([pp_widget, upload_widget, view_widget])
        self.tab.set_title(0, 'Phase Plane')
        self.tab.set_title(1, 'Drive Uploader')
        self.tab.set_title(2, 'Surface Viewer')

    def show(self):
        display(self.tab)

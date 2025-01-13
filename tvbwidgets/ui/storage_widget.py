# -*- coding: utf-8 -*-
#
# "TheVirtualBrain - Widgets" package
#
# (c) 2022-2025, TVB Widgets Team
#
import ipywidgets

from tvbwidgets.ui.base_widget import TVBWidget
from tvbwidgets.ui.bucket_widget import BucketWidget
from tvbwidgets.ui.drive_widget import DriveWidget


class StorageWidget(ipywidgets.Tab, TVBWidget):

    def __init__(self, collab=None, folder=None, selected_storage=0, **kwargs):
        self.tab1 = DriveWidget(collab, folder)
        self.tab2 = BucketWidget()

        super().__init__([self.tab1, self.tab2], selected_index=selected_storage,
                         layout=ipywidgets.Layout(width='550px', height='200px'), **kwargs)

        self.set_title(0, 'Drive')
        self.set_title(1, 'Bucket')
        self.drive_api = self.tab1
        self.bucket_api = self.tab2

    def get_selected_file_content(self):
        api = self.retrieve_api()
        return api.get_selected_file_content()

    def get_selected_file_name(self):
        api = self.retrieve_api()
        filename = api.get_selected_file_path()
        return filename

    def retrieve_api(self):
        if self.selected_index == 0:
            return self.drive_api
        else:
            return self.bucket_api

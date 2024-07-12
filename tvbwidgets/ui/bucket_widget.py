# -*- coding: utf-8 -*-
#
# "TheVirtualBrain - Widgets" package
#
# (c) 2022-2024, TVB Widgets Team
#

import ipywidgets
import requests
from tvb_ext_bucket.ebrains_drive_wrapper import BucketWrapper
from tvbwidgets.ui.base_widget import TVBWidget


class BucketWidget(ipywidgets.VBox, TVBWidget):

    def __init__(self, **kwargs):
        TVBWidget.__init__(self, **kwargs)
        self.client = BucketWrapper()

        try:
            all_buckets = self.client.list_buckets()
        except Exception:
            self.logger.error("Could not retrieve the list of available Buckets!")
            all_buckets = []
        layout = ipywidgets.Layout(width='400px')
        self.buckets_dropdown = ipywidgets.Dropdown(description='Bucket', value=None,
                                                    options=all_buckets, layout=layout)
        self.files_list = ipywidgets.Select(description='Files', value=None, disabled=False, layout=layout)

        self.buckets_dropdown.observe(self.select_bucket, names='value')

        self._parent_dir = None
        self._map_names_to_files = dict()
        ipywidgets.VBox.__init__(self, [self.buckets_dropdown, self.files_list], **kwargs)

    def get_chosen_bucket(self):
        return self.buckets_dropdown.value

    def get_selected_file_path(self):
        return self.buckets_dropdown.value + "/" + self.files_list.value

    def get_selected_file_content(self):
        path = self.files_list.value
        downloadable_url = self.client.get_download_url(path, self.buckets_dropdown.value)
        response = requests.get(downloadable_url)
        return response.content

    def select_bucket(self, _):
        selected_bucket = self.buckets_dropdown.value
        self.files_list.options = self.client.get_files_in_bucket(selected_bucket)

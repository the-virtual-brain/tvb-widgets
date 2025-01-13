# -*- coding: utf-8 -*-
#
# "TheVirtualBrain - Widgets" package
#
# (c) 2022-2025, TVB Widgets Team
#

import ipywidgets
import requests
from tvbwidgets.core.auth import get_current_token
from tvbwidgets.core.bucket.bucket_api import ExtendedBucketApiClient
from tvbwidgets.ui.base_widget import TVBWidget
from ebrains_drive.files import DataproxyFile


class BucketWidget(ipywidgets.VBox, TVBWidget):

    def __init__(self, **kwargs):
        TVBWidget.__init__(self, **kwargs)
        bearer_token = get_current_token()
        self.client = ExtendedBucketApiClient(token=bearer_token)

        try:
            list_buckets = self.client.buckets.list_buckets()
            buckets_name = [b.name for b in list_buckets]
        except Exception:
            self.logger.error("Could not retrieve the list of available Buckets!")
            buckets_name = []
        layout = ipywidgets.Layout(width='400px')
        self.buckets_dropdown = ipywidgets.Dropdown(description='Bucket', value=None,
                                                    options=buckets_name, layout=layout)
        self.files_list = ipywidgets.Select(description='Files', value=None, disabled=False, layout=layout)

        self.buckets_dropdown.observe(self.select_bucket, names='value')

        ipywidgets.VBox.__init__(self, [self.buckets_dropdown, self.files_list], **kwargs)

    def get_selected_bucket(self):
        return self.buckets_dropdown.value

    def get_selected_file_path(self):
        file = self.files_list.value
        if file is None:
            return file
        return self.get_selected_bucket() + "/" + file

    def get_selected_file_content(self):
        file_path = self.files_list.value
        bucket_name = self.get_selected_bucket()
        dataproxy_file = self._get_dataproxy_file(file_path, bucket_name)
        response = requests.get(dataproxy_file.get_download_link())
        return response.content

    def select_bucket(self, _):
        selected_bucket = self.get_selected_bucket()
        bucket = self.client.buckets.get_bucket(selected_bucket)
        self.files_list.options = [f.name for f in bucket.ls()]

    def _get_dataproxy_file(self, file_path, bucket_name):
        # type: (str, str) -> DataproxyFile
        """
        Get the DataProxy file corresponding to the path <file_path> in bucket <bucket_name>
        """
        file_path = file_path.lstrip('/')
        bucket = self.client.buckets.get_bucket(bucket_name)
        # find first dataproxy file corresponding to provided path
        dataproxy_file = next((f for f in bucket.ls() if f.name == file_path), None)
        return dataproxy_file

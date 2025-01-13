# -*- coding: utf-8 -*-
#
# "TheVirtualBrain - Widgets" package
#
# (c) 2022-2025, TVB Widgets Team
#

import os
import ipywidgets
import ebrains_drive
from ebrains_drive.exceptions import DoesNotExist
from tvbwidgets.core.auth import get_current_token
from tvbwidgets.ui.base_widget import TVBWidget


class DriveWidget(ipywidgets.VBox, TVBWidget):
    ROOT = '/'
    PARENT_DIR = '..'
    DIR_ICON = '\U0001F4C1'

    def __init__(self, collab=None, folder=None, **kwargs):
        TVBWidget.__init__(self, **kwargs)
        self.collab = collab
        self.folder = folder
        bearer_token = get_current_token()
        self.client = ebrains_drive.connect(token=bearer_token)

        try:
            all_repos = self.client.repos.list_repos()
        except Exception:
            self.logger.error("Could not retrieve Repos from EBRAINS Drive!")
            all_repos = []
        dropdown_options = {repo.name: repo for repo in all_repos}

        layout = ipywidgets.Layout(width='400px')
        self.repos_dropdown = ipywidgets.Dropdown(description='Repository', value=dropdown_options.get(self.collab),
                                                  options=dropdown_options, layout=layout)
        self.files_list = ipywidgets.Select(description='Files', value=None, disabled=False, layout=layout)

        self.repos_dropdown.observe(self.select_repo, names='value')
        self.files_list.observe(self.select_dir, names='value')

        self._parent_dir = None
        self._map_names_to_files = dict()

        if self.collab:
            self.select_repo(None, folder=self.folder)
            if self.collab not in list(dropdown_options):
                self.logger.warning(f"Could not find the Collab: {self.collab}. You can manually browse for it.")

        ipywidgets.VBox.__init__(self, [self.repos_dropdown, self.files_list], **kwargs)

    def get_chosen_repo(self):
        return self.repos_dropdown.value

    def get_selected_file_path(self):
        file = self._map_names_to_files.get(self.files_list.value)
        if file is None:
            return file
        return file.path

    def get_selected_file_content(self):
        repo_obj = self.get_chosen_repo()
        file_obj = repo_obj.get_file(self.get_selected_file_path())
        return file_obj.get_content()

    def select_repo(self, _, folder=None):
        if folder is None:
            folder = self.ROOT
        if not folder.startswith(self.ROOT):
            folder = self.ROOT + folder
        self.update_files_for_chosen_dir(folder)

    def select_dir(self, _):
        current_selection = self._map_names_to_files.get(self.files_list.value)
        if not current_selection or not current_selection.isdir:
            return
        self.update_files_for_chosen_dir(current_selection.path)

    def update_files_for_chosen_dir(self, selected_dir):
        self.files_list.unobserve(self.select_dir, names='value')
        try:
            selected_repo = self.get_chosen_repo()
            self.logger.debug("Update Files called with {} and {}".format(selected_repo, selected_dir))
            self._gather_files(selected_repo, selected_dir)
            self.files_list.options = list(self._map_names_to_files.keys())
            self.files_list.value = None
        except Exception as e:
            self.logger.info(e)
            raise e
        finally:
            self.files_list.observe(self.select_dir, names='value')

    def _gather_files(self, repo, sub_folder):
        dir_icon = self.DIR_ICON

        try:
            dir_obj = repo.get_dir(sub_folder)
            if sub_folder == self.ROOT:
                self._parent_dir = None
            else:
                self._parent_dir = repo.get_dir(os.path.dirname(dir_obj.path))
            self._map_names_to_files = {self.PARENT_DIR: self._parent_dir}

            files_in_repository = dir_obj.ls(force_refresh=True)

            for file in files_in_repository:
                filename = file.name
                if file.isdir:
                    filename = dir_icon + filename
                self._map_names_to_files.update({filename: file})
        except DoesNotExist:
            self.logger.error("Folder {} could not be accessed".format(sub_folder))


class DriveUploadWidget(ipywidgets.HBox, TVBWidget):

    def __init__(self, **kwargs):
        self.repo_browser = DriveWidget()

        self.upload = ipywidgets.FileUpload(description="Choose file", multiple=False)

        self.upload_button = ipywidgets.Button(description="Upload")

        def on_upload_change(s):
            self.logger.debug("Uploading file to drive...")
            upload_value_dict = self.upload.value
            content = list(upload_value_dict.values())[0]['content']
            filename = list(upload_value_dict)[0]
            local_filename = os.path.join(".temp", filename)
            os.makedirs(".temp", exist_ok=True)
            self.logger.debug("Storing local {} ".format(local_filename))
            with open(local_filename, "wb") as fp:
                fp.write(content)

            selected_repo = self.repo_browser.get_chosen_repo()
            selected_dir = self.repo_browser.get_chosen_dir()
            selected_dir = selected_repo.get_dir(selected_dir)

            selected_dir.upload_local_file(local_filename)
            os.remove(local_filename)
            self.logger.info("Finished upload {}!".format(filename))
            self.repo_browser.update_files_for_chosen_repo()

        self.upload_button.on_click(on_upload_change)

        super().__init__([ipywidgets.VBox([self.upload, self.upload_button]),
                          self.repo_browser], **kwargs)

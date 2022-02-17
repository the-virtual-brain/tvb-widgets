# -*- coding: utf-8 -*-
#
# "TheVirtualBrain - Widgets" package
#
# (c) 2022-2023, TVB Widgets Team
#

import os
import ipywidgets
import ebrains_drive
from ebrains_drive.exceptions import DoesNotExist
from tvbwidgets.auth import get_current_token
from tvbwidgets.ui.base_widget import TVBWidget


class DriveWidget(ipywidgets.VBox, TVBWidget):
    ROOT = "/"

    def __init__(self, **kwargs):
        bearer_token = get_current_token()
        self.client = ebrains_drive.connect(token=bearer_token)

        repos_label = ipywidgets.Label("Repository")
        all_repos = self.client.repos.list_repos()
        dropdown_options = [(repo.name, repo) for repo in all_repos]
        self.repos_dropdown = ipywidgets.Dropdown(options=dropdown_options)

        dirs_label = ipywidgets.Label("Directories in repository")
        self.dirs_dropdown = ipywidgets.Dropdown()

        files_label = ipywidgets.Label("Files in folder")
        self.files_list = ipywidgets.Textarea(disabled=True,
                                              layout={'width': '300',
                                                      'height': '200'})

        self._update_dirs_for_chosen_repo()

        def search_dirs(change):
            if change['type'] == 'change' and change['name'] == 'value':
                self._update_dirs_for_chosen_repo()

        def search_files(change):
            if change['type'] == 'change' and change['name'] == 'value':
                self.update_files_for_chosen_repo()

        self.repos_dropdown.observe(search_dirs)
        self.dirs_dropdown.observe(search_files)

        super().__init__([ipywidgets.HBox([repos_label, self.repos_dropdown]),
                          ipywidgets.HBox([dirs_label, self.dirs_dropdown]),
                          ipywidgets.HBox([files_label, self.files_list])], **kwargs)

    def get_chosen_repo(self):
        return self.repos_dropdown.value

    def get_chosen_dir(self):
        return self.dirs_dropdown.value

    def _update_dirs_for_chosen_repo(self):
        selected_repo = self.get_chosen_repo()
        selected_dir = self.ROOT
        dirs_list = [selected_dir]

        try:
            dir_obj = selected_repo.get_dir(selected_dir)
            files_in_repository = dir_obj.ls(force_refresh=True)

            for file in files_in_repository:
                if hasattr(file, "entries"):
                    dirs_list.append(os.path.join(selected_dir, file.name))
        except DoesNotExist:
            self.logger.error("Folder {} could not be accessed".format(selected_dir))
            pass

        self.dirs_dropdown.options = dirs_list

    def update_files_for_chosen_repo(self):
        selected_repo = self.get_chosen_repo()
        selected_dir = self.get_chosen_dir() or self.ROOT
        self.logger.debug("Update Files called with {} and {}".format(selected_repo, selected_dir))
        files_list = []
        self._gather_files(selected_repo, selected_dir, files_list)
        self.files_list.value = '\n'.join(files_list)

    def _gather_files(self, repo, sub_folder, files_list):
        try:
            dir_obj = repo.get_dir(sub_folder)
            files_in_repository = dir_obj.ls(force_refresh=True)

            for file in files_in_repository:
                if hasattr(file, "entries"):
                    self._gather_files(repo, self.ROOT + file.name, files_list)
                else:
                    files_list.append(os.path.join(sub_folder, file.name))
        except DoesNotExist:
            self.logger.error("Folder {} could not be accessed".format(sub_folder))
            pass

    def get_file_content(self, filename):
        chosen_repo = self.get_chosen_repo()
        chosen_dir = self.dirs_dropdown.value

        file_path = os.path.join(chosen_dir, filename)
        ref_file = chosen_repo.get_file(file_path)
        file_content = ref_file.get_content()

        return file_content


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

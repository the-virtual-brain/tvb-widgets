import ipywidgets
from ebrains_drive.exceptions import DoesNotExist

from tvbwidgets.repo_browser_widget import RepoBrowserWidget


class DriveUploadWidget(object):
    def __init__(self):
        self.repo_browser = RepoBrowserWidget()

        self.upload = ipywidgets.FileUpload(description="Choose file", multiple=False)

        self.upload_button = ipywidgets.Button(description="Upload")

        def on_upload_change(s):
            print("Uploading file to drive...")
            upload_value_dict = self.upload.value
            content = list(upload_value_dict.values())[0]['content']
            filename = list(upload_value_dict)[0]
            local_file = "./" + filename
            with open(local_file, "wb") as fp:
                fp.write(content)

            selected_repo = self.repo_browser.get_chosen_repo()
            seafdir = selected_repo.get_dir('/')
            try:
                # TODO: Bug in ebrains_drive API: cannot upload in root folder, so we use a subdirectory
                new_dir = selected_repo.get_dir('/spatial')
            except DoesNotExist:
                new_dir = seafdir.mkdir('spatial')
            file = new_dir.upload_local_file(local_file)

        self.upload_button.on_click(on_upload_change)

    def get_widget(self):
        vbox = ipywidgets.HBox([self.upload,
                                self.repo_browser.get_widget(),
                                self.upload_button])
        return vbox

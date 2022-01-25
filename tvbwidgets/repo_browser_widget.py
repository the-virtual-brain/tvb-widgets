import ebrains_drive
import ipywidgets
from ebrains_drive.exceptions import DoesNotExist


class RepoBrowserWidget(object):

    def __init__(self):
        # bearer_token = clb_oauth.get_token()
        bearer_token = 'eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJfNkZVSHFaSDNIRmVhS0pEZDhXcUx6LWFlZ3kzYXFodVNJZ1RXaTA1U2k0In0.eyJleHAiOjE2NDMyMDc4MDMsImlhdCI6MTY0MjYwMzAwMywiYXV0aF90aW1lIjoxNjQyNTczMjM3LCJqdGkiOiJjMzFhMGJmMS03ZTU3LTQ5MWEtOGNkYi0zMDJlNWQxMzVjYTQiLCJpc3MiOiJodHRwczovL2lhbS5lYnJhaW5zLmV1L2F1dGgvcmVhbG1zL2hicCIsImF1ZCI6WyJyZWFsbS1tYW5hZ2VtZW50IiwianVweXRlcmh1Yi1vcGVuc2hpZnQtcHJldmlldyIsImp1cHl0ZXJodWIiLCJzdW1taXQtcmVnaXN0cmF0aW9uIiwib3BlbnNoaWZ0IiwieHdpa2kiLCJ0ZWFtIiwib3BlbnNoaWZ0LWpzYyIsImFjY291bnQiLCJvcGVuc2hpZnQtZGV2IiwiZ3JvdXAiXSwic3ViIjoiMzY3MjQ4OWEtOGI4ZS00NGFkLWI4M2ItNTQ2MzNjYjVhNzVlIiwidHlwIjoiQmVhcmVyIiwiYXpwIjoianVweXRlcmh1Yi1qc2MiLCJzZXNzaW9uX3N0YXRlIjoiMWNmYTFiMWMtZDIzYS00N2I0LTllNDYtZTI4NzY3YjhhN2IxIiwiYWNyIjoiMCIsImFsbG93ZWQtb3JpZ2lucyI6WyJodHRwczovL2xhYi5qc2MuZWJyYWlucy5ldSJdLCJyZWFsbV9hY2Nlc3MiOnsicm9sZXMiOlsiY29sbGFib3JhdG9yeV9tZW1iZXIiLCJvZmZsaW5lX2FjY2VzcyIsInVtYV9hdXRob3JpemF0aW9uIl19LCJzY29wZSI6InByb2ZpbGUgY29sbGFiLmRyaXZlIG9mZmxpbmVfYWNjZXNzIGNsYi53aWtpLndyaXRlIGdyb3VwIGNsYi53aWtpLnJlYWQgdGVhbSBjbGIuZHJpdmU6d3JpdGUgcm9sZXMgZW1haWwgb3BlbmlkIGNsYi5kcml2ZTpyZWFkIiwiZW1haWxfdmVyaWZpZWQiOnRydWUsIm5hbWUiOiJQYXVsYSBQb3BhIiwibWl0cmVpZC1zdWIiOiIzMDc0NDEiLCJwcmVmZXJyZWRfdXNlcm5hbWUiOiJwYXVsYXBvcGEiLCJnaXZlbl9uYW1lIjoiUGF1bGEiLCJmYW1pbHlfbmFtZSI6IlBvcGEiLCJlbWFpbCI6InBhdWxhLnBvcGFAY29kZW1hcnQucm8ifQ.Ajid5ZNvwU6H2coFmF7oGyw5uWktNrcvXjfAQEy3MpTVydtS5WjkDq2flZ09VtakoYnb6AuG-Whsakz6tIDUEBbf-izOIjVUPtuzgUE3wOAWJjCzAndpejv7pOeHTExyBXrYrnCLrIkjqzzyNrTH2Hxs7RIKbHP8zQV5FvQCEv1294dgSpzFIo4u4c6s79GlKqAWsuHUA6IBLNJd2wzBAWGoVk-lHu6FMfYF7owDWJb7zcBtZwe0C08lw-3he5iidMMVZbmLYQ-ySNzFG1H3PJLXDZfSdT0SRu7jS61HFMj0Arb3SsIxdgGKdSlhWdSpV6sx8k_N2pVk6yKbotUMBA'

        self.client = ebrains_drive.connect(token=bearer_token)

    def get_widget(self):
        repos_label = ipywidgets.Label("Repository")
        all_repos = self.get_repos()
        dropdown_options = [(repo.name, repo) for repo in all_repos]
        self.repos_dropdown = ipywidgets.Dropdown(options=dropdown_options)

        files_label = ipywidgets.Label("Files in repository")
        self.files_dropdown = ipywidgets.Dropdown()

        dirs_label = ipywidgets.Label("Directories in repository")
        self.dirs_dropdown = ipywidgets.Dropdown()

        self.update_contents_for_chosen_repo()

        def search_content(change):
            if change['type'] == 'change' and change['name'] == 'value':
                self.update_contents_for_chosen_repo()

        self.repos_dropdown.observe(search_content)

        vbox = ipywidgets.HBox([ipywidgets.VBox([ipywidgets.HBox([repos_label, self.repos_dropdown]),
                                                 ipywidgets.HBox([files_label, self.files_dropdown]),
                                                 ipywidgets.HBox([dirs_label, self.dirs_dropdown])])])
        return vbox

    def get_chosen_repo(self):
        return self.repos_dropdown.value

    def get_repos(self):
        list_repos = self.client.repos.list_repos()
        return list_repos

    def _get_full_filename(self, subfolder, filename):
        separator = '/'
        if subfolder == separator:
            return subfolder + filename
        else:
            return subfolder + separator + filename

    def _gather_files(self, repo, subfolder, files_list, dirs_list):
        try:
            dir_obj = repo.get_dir(subfolder)
            files_in_repository = dir_obj.ls(force_refresh=True)

            for file in files_in_repository:
                if hasattr(file, "entries"):
                    dirs_list.append(self._get_full_filename(subfolder, file.name))
                    self._gather_files(repo, '/' + file.name, files_list, dirs_list)
                else:
                    files_list.append(self._get_full_filename(subfolder, file.name))
        except DoesNotExist as e:
            print("Folder {} could not be accesed".format(subfolder))
            pass

    def update_contents_for_chosen_repo(self):
        selected_repo = self.get_chosen_repo()

        files_list = []
        dirs_list = []

        self._gather_files(selected_repo, '/', files_list, dirs_list)

        self.files_dropdown.options = files_list
        self.dirs_dropdown.options = dirs_list

    def get_file_content(self, filename):
        chosen_repo = self.get_chosen_repo()
        chosen_dir = self.dirs_dropdown.value

        filepath = chosen_dir + '/' + filename

        seaffile = chosen_repo.get_file(filepath)
        file_content = seaffile.get_content()
        return file_content

import logging
import os
from urllib.error import HTTPError
from pkg_resources import get_distribution
import pyunicore.client as unicore_client
from pyunicore.helpers.jobs import Status as unicore_status
from pyunicore.credentials import AuthenticationFailedException
from datetime import datetime
from tvbwidgets.core.auth import get_current_token
log = logging.getLogger(__name__)


class HPCLaunch(object):
    storage_name = {'DAINT-CSCS': 'HOME', 'JUSUF': 'PROJECT'}
    env_dir = 'tvb_widgets_test'
    env_name = 'venv_test'
    python_dir = {'DAINT-CSCS': 'python3.9', 'JUSUF': 'python3.10'}
    modules = {'DAINT-CSCS': 'cray-python', 'JUSUF': 'Python'}
    pip_libraries = 'tvb-widgets tvb-data joblib'
    EXECUTABLE_KEY = 'Executable'
    PROJECT_KEY = 'Project'
    JOB_TYPE_KEY = 'Job type'
    INTERACTIVE_KEY = 'interactive'
    project = 'icei-hbp-2021-0007'

    def __init__(self, site, param1, param2, param1_values, param2_values, metrics, file_name):
        self.site = site
        self.param1 = param1
        self.param2 = param2
        self.param1_values = param1_values
        self.param2_values = param2_values
        self.metrics = metrics
        self.file_name = file_name
        self.submit_job("parameters.py", ["C:\\Users\\teodora.misan\\Documents\\tvb-widgets\\tvbwidgets\\core\\pse\\parameters.py"], True)

    @property
    def _activate_command(self):
        return f'source ${self.storage_name[self.site]}/{self.env_dir}/{self.env_name}/bin/activate'

    @property
    def _module_load_command(self):
        return f'module load {self.modules.get(self.site, "")}'

    @property
    def _create_env_command(self):
        return f'cd ${self.storage_name[self.site]}/{self.env_dir} ' \
               f'&& rm -rf {self.env_name} ' \
               f'&& python -mvenv {self.env_name}'  # why is -mvenv and not -m env?

    @property
    def _install_dependencies_command(self):
        return f'pip install -U pip && pip install allensdk && pip install {self.pip_libraries}'

    def connect_client(self):
        log.info(f"Connecting to {self.site}...")
        token = get_current_token()
        transport = unicore_client.Transport(token)
        registry = unicore_client.Registry(transport, unicore_client._HBP_REGISTRY_URL)

        try:
            sites = registry.site_urls
        except Exception:
            log.error("Unicore seems to be down at the moment. "
                      "Please check service availability and try again later")
            return None

        try:
            site_url = sites['JUSUF']
        except KeyError:
            log.error(f'Site {self.site} seems to be down for the moment.')
            return None

        try:
            client = unicore_client.Client(transport, site_url)
        except (AuthenticationFailedException, HTTPError):
            log.error(f'Authentication to {self.site} failed, you might not have permissions to access it.')
            return None

        log.info(f'Authenticated to {self.site} with success.')
        return client

    def _check_environment_ready(self, home_storage):
        # Pyunicore listdir method returns directory names suffixed by '/'
        if f"{self.env_dir}/" not in home_storage.listdir():
            home_storage.mkdir(self.env_dir)
            log.info(f"Environment directory not found in HOME, will be created.")
            return False

        if f"{self.env_dir}/{self.env_name}/" not in home_storage.listdir(self.env_dir):
            log.info(f"Environment not found in HOME, will be created.")
            return False

        try:
            # Check whether tvb-widgets is installed in HPC env and if version is updated
            site_packages_path = f'{self.env_dir}/{self.env_name}/lib/{self.python_dir[self.site]}/site-packages'
            site_packages = home_storage.listdir(site_packages_path)
            files = [file for file in site_packages if "tvb_widgets" in file]
            assert len(files) >= 1
            remote_version = files[0].split("tvb_widgets-")[1].split('.dist-info')[0]

            # Should have a class which returns the version(as in tvbextxircuits) ?
            local_version = get_distribution("tvb-widgets").version
            if remote_version != local_version:
                log.info(f"Found an older version {remote_version} of tvb-widgets installed in the "
                         f"environment, will recreate it with {local_version}.")
                return False
            return True
        except HTTPError as e:
            log.info(f"Could not find site-packages in the environment, will recreate it: {e}")
            return False
        except AssertionError:
            log.info(f"Could not find tvb-widgets installed in the environment, will recreate it.")
            return False
        except IndexError:
            log.info(f"Could not find tvb-widgets installed in the environment, will recreate it.")
            return False

    def _search_for_home_dir(self, client):
        log.info(f"Accessing storages on {self.site}...")
        num = 10
        offset = 0
        storages = client.get_storages(num=num, offset=offset)
        while len(storages) > 0:
            for storage in storages:
                if storage.resource_url.endswith(self.storage_name[self.site]):
                    return storage
            offset += num
            storages = client.get_storages(num=num, offset=offset)
        return None

    def _format_date_for_job(self, job):
        date = datetime.strptime(job.properties['submissionTime'], '%Y-%m-%dT%H:%M:%S+%f')
        return date.strftime('%m.%d.%Y, %H_%M_%S')

    def submit_job(self, executable, inputs, do_stage_out):
        client = self.connect_client()
        if client is None:
            log.error(f"Could not connect to {self.site}, stopping execution.")
            return

        home_storage = self._search_for_home_dir(client)
        if home_storage is None:
            log.error(f"Could not find a {self.storage_name[self.site]} storage on {self.site}, stopping execution.")
            return

        is_env_ready = self._check_environment_ready(home_storage)
        if is_env_ready:
            log.info(f"Environment is already prepared, it won't be recreated.")
        else:
            log.info(f"Preparing environment in your {self.storage_name[self.site]} folder...")
            job_description = {
                self.EXECUTABLE_KEY: f"{self._module_load_command} && {self._create_env_command} && "
                                     f"{self._activate_command} && {self._install_dependencies_command}",
                self.PROJECT_KEY: self.project,
                self.JOB_TYPE_KEY: self.INTERACTIVE_KEY}
            job_env_prep = client.new_job(job_description, inputs=[])
            log.info(f"Job is running at {self.site}: {job_env_prep.working_dir.properties['mountPoint']}. "
                     f"Submission time is: {self._format_date_for_job(job_env_prep)}. "
                     f"Waiting for job to finish..."
                     f"It can also be monitored interactively with the Monitor HPC button.")
            job_env_prep.poll()
            if job_env_prep.properties['status'] == unicore_status.FAILED:
                log.error(f"Encountered an error during environment setup, stopping execution.")
                return
            log.info(f"Successfully finished the environment setup.")

        log.info("Launching workflow...")
        job_description = {
            self.EXECUTABLE_KEY: f"{self._module_load_command} && {self._activate_command} && "
                                 f"python {executable} {self.param1} {self.param2} '{self.param1_values}'  "
                                 f"'{self.param2_values}' {self.file_name}",
            self.PROJECT_KEY: self.project}
        job_workflow = client.new_job(job_description, inputs=inputs)
        log.info(f"Job is running at {self.site}: {job_workflow.working_dir.properties['mountPoint']}. "
                 f"Submission time is: {self._format_date_for_job(job_workflow)}.")
        log.info('Finished remote launch.')

        if do_stage_out:
            self.monitor_job(job_workflow)
        else:
            log.info('You can use Monitor HPC button to monitor it.')

    def monitor_job(self, job):
        log.info('Waiting for job to finish...'
                 'It can also be monitored interactively with the Monitor HPC button.')
        job.poll()

        if job.properties['status'] == unicore_status.FAILED:
            log.error(f"Job finished with errors.")
            return
        log.info(f"Job finished with success. Staging out the results...")
        self.stage_out_results(job)
        log.info(f"Finished execution.")

    def stage_out_results(self, job):
        content = job.working_dir.listdir()

        storage_config_file = content.get(self.file_name)
        if storage_config_file is None:
            log.info(f"Could not find file: {self.file_name}")
            log.info("Could not finalize the stage out. "
                     "Please download your results manually using the Monitor HPC button.")
            return
        else:
            storage_config_file.download(self.file_name)
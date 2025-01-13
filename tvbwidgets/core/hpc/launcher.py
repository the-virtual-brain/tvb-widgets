# -*- coding: utf-8 -*-
#
# "TheVirtualBrain - Widgets" package
#
# (c) 2022-2025, TVB Widgets Team
#

import time
import pyunicore.client
from pathlib import Path
from typing import Callable
from datetime import datetime
from urllib.error import HTTPError
from pyunicore.helpers.jobs import Description
from pyunicore.client import JobStatus
from pyunicore.credentials import AuthenticationFailedException, OIDCToken
from pkg_resources import get_distribution, DistributionNotFound
from tvbwidgets.core.auth import get_current_token
from tvbwidgets.core.hpc.config import HPCConfig
from tvbwidgets.core.logger.builder import get_logger
from tvbwidgets.core.pse.parameters import PROGRESS_STATUS
from tvb.simulator.simulator import Simulator
from tvbwidgets.core.pse.storage import StoreObj
from tvbwidgets.core.pse.toml_storage import TOMLStorage

LOGGER = get_logger(__name__)


class HPCLaunch(object):
    pip_libraries = 'tvb-widgets tvb-data'
    EXECUTABLE_KEY = 'Executable'
    PROJECT_KEY = 'Project'
    JOB_TYPE_KEY = 'Job type'
    INTERACTIVE_KEY = 'interactive'

    def __init__(self, simulator, hpc_config, param1, param2, param1_values, param2_values, metrics, file_name,
                 update_progress):
        # type: (Simulator, HPCConfig, str, str, list, list, list, str, Callable) -> None
        self.config = hpc_config
        self.param1 = param1
        self.param2 = param2
        self.param1_values = param1_values
        self.param2_values = param2_values
        self.metrics = metrics
        self.file_name = file_name
        self.update_progress = update_progress
        serialized_config = self._serialize_configuration(simulator)
        self.submit_job("tvbwidgets.core.pse.parameters", serialized_config, True)

    @property
    def _activate_command(self):
        return f'source ${self.config.storage_name}/{self.config.env_dir}/{self.config.env_name}/bin/activate'

    @property
    def _module_load_command(self):
        return f'module load {self.config.module_to_load}'

    @property
    def _create_env_command(self):
        return f'cd ${self.config.storage_name}/{self.config.env_dir} ' \
               f'&& rm -rf {self.config.env_name} ' \
               f'&& python -mvenv {self.config.env_name}'

    @property
    def _install_dependencies_command(self):
        return f'pip install -U pip && pip install {self.pip_libraries}'

    def _serialize_configuration(self, sim):
        # type: (Simulator) -> Path
        return TOMLStorage.write_pse_in_file(StoreObj(sim, self.param1, self.param2, self.param1_values,
                                                      self.param2_values, self.metrics, self.config.n_threads,
                                                      self.file_name))

    def connect_client(self):
        LOGGER.info(f"Connecting to {self.config.site}...")
        token = OIDCToken(get_current_token())
        transport = pyunicore.client.Transport(token)
        registry = pyunicore.client.Registry(transport, pyunicore.client._HBP_REGISTRY_URL)

        try:
            sites = registry.site_urls
        except Exception:
            LOGGER.error("Unicore seems to be down at the moment. "
                         "Please check service availability and try again later")
            return None

        try:
            site_url = sites[self.config.site]
        except KeyError:
            LOGGER.error(f'Site {self.config.site} seems to be down for the moment.')
            return None

        try:
            client = pyunicore.client.Client(transport, site_url)
        except (AuthenticationFailedException, HTTPError):
            LOGGER.error(f'Authentication to {self.config.site} failed, you might not have permissions to access it.')
            return None

        LOGGER.info(f'Authenticated to {self.config.site} with success.')
        return client

    def _check_environment_ready(self, home_storage):
        # Pyunicore listdir method returns directory names suffixed by '/'
        if f"{self.config.env_dir}/" not in home_storage.listdir():
            home_storage.mkdir(self.config.env_dir)
            LOGGER.info("Environment directory not found in HOME, will be created.")
            return False

        if f"{self.config.env_dir}/{self.config.env_name}/" not in home_storage.listdir(self.config.env_dir):
            LOGGER.info("Environment not found in HOME, will be created.")
            return False

        try:
            # Check whether tvb-widgets is installed in HPC env and if version is updated
            site_packages_path = f'{self.config.env_dir}/{self.config.env_name}/lib/{self.config.python_dir}/site-packages'
            site_packages = home_storage.listdir(site_packages_path)
            files = [file for file in site_packages if "tvb_widgets" in file]
            assert len(files) >= 1
            remote_version = files[0].split("tvb_widgets-")[1].split('.dist-info')[0]
            LOGGER.info(f'Found tvb-widgets version: {remote_version} remotely!')

            try:
                local_version = get_distribution("tvb-widgets").version
                if remote_version != local_version:
                    LOGGER.info(f"Found a different remote version {remote_version} of tvb-widgets  "
                                f"installed on the HPC environment, than the local {local_version}, "
                                f"we will recreate env from Pipy to hopefully match.")
                    return False
            except DistributionNotFound:
                # If local installation is from sources, then we can not install it remotely from Pypi
                pass

            return True
        except Exception:
            LOGGER.exception("could not match tvb-widgets ...")
            LOGGER.info("Could not match tvb-widgets installed in the environment, will recreate it.")
            return False

    def _search_for_home_dir(self, client):
        LOGGER.info(f"Accessing storages on {self.config.site}...")
        num = 10
        offset = 0
        storages = client.get_storages(num=num, offset=offset)
        while len(storages) > 0:
            for storage in storages:
                if storage.resource_url.endswith(self.config.storage_name):
                    return storage
            offset += num
            storages = client.get_storages(num=num, offset=offset)
        return None

    @staticmethod
    def _format_date_for_job(job):
        date = datetime.strptime(job.properties['submissionTime'], '%Y-%m-%dT%H:%M:%S+%f')
        return date.strftime('%m.%d.%Y, %H_%M_%S')

    def submit_job(self, executable, path_input, do_stage_out):
        # type (str, Path, bool) -> None
        client = self.connect_client()
        if client is None:
            LOGGER.error(f"Could not connect to {self.config.site}, stopping execution.")
            return

        home_storage = self._search_for_home_dir(client)
        if home_storage is None:
            LOGGER.error(
                f"Could not find a {self.config.storage_name} storage on {self.config.site}, stopping execution.")
            return

        is_env_ready = self._check_environment_ready(home_storage)
        if is_env_ready:
            LOGGER.info("Environment is already prepared, it won't be recreated.")
        else:
            LOGGER.info(f"Preparing environment in your {self.config.storage_name} folder...")
            job_description = {
                self.EXECUTABLE_KEY: f"{self._module_load_command} && {self._create_env_command} && "
                                     f"{self._activate_command} && {self._install_dependencies_command}",
                self.PROJECT_KEY: self.config.project,
                self.JOB_TYPE_KEY: self.INTERACTIVE_KEY}
            job_env_prep = client.new_job(job_description, inputs=[])
            LOGGER.info(f"Job is running at {self.config.site}: {job_env_prep.working_dir.properties['mountPoint']}. "
                        f"Submission time is: {self._format_date_for_job(job_env_prep)}. "
                        f"Waiting for job to finish..."
                        f'It can also be monitored with the "PyUnicore tasks stream" tool on the right-side bar.')
            job_env_prep.poll()
            if job_env_prep.properties['status'] == JobStatus.FAILED:
                LOGGER.error("Encountered an error during environment setup, stopping execution.")
                return
            LOGGER.info("Successfully finished the environment setup.")

        command = f"{self._module_load_command} && {self._activate_command} && " \
                  f"python -m {executable} {path_input}"
        LOGGER.info(f"Launching workflow for command: \n {command}")
        job = Description(
            executable=command,
            project=self.config.project,
            resources=self.config.resources
        )
        job_workflow = client.new_job(job.to_dict(), inputs=[path_input.as_posix()])
        LOGGER.info(f"Job is running at {self.config.site}: {job_workflow.working_dir.properties['mountPoint']}. "
                    f"Submission time is: {self._format_date_for_job(job_workflow)}.")
        LOGGER.info('Finished remote launch.')

        if do_stage_out:
            self.monitor_job(job_workflow)
        else:
            LOGGER.info('You can use "PyUnicore Tasks Stream" tool to monitor it.')

    @staticmethod
    def read_file_from_hpc(job, file_name):
        try:
            content = job.working_dir.listdir()
            storage_config_file = content.get(file_name)
            if storage_config_file is None:
                LOGGER.warning(f"Could not find file: {file_name}")
                return 0
            return storage_config_file.raw().read()
        except Exception as e:
            LOGGER.error(f"Could not read file: {file_name}", exc_info=e)
            return 0

    def monitor_job(self, job):
        LOGGER.info('Waiting for job to finish...'
                    'It can also be monitored interactively with the "PyUnicore Tasks Stream" tool.')

        start_time = int(time.time())
        # we replaced job.poll to our custom while, to update the progress bar as well
        while job.status.ordinal() < JobStatus.SUCCESSFUL.ordinal():
            completed_count = int(self.read_file_from_hpc(job, PROGRESS_STATUS))
            self.update_progress(completed_count)
            time.sleep(2)
            if self.config.timeout > 0 and int(time.time()) > start_time + self.config.timeout:
                # signalize a problem in the front-end
                self.update_progress(error_msg="Connection Timeout")
                raise TimeoutError(f"Timeout waiting for job to complete. Already completed {completed_count}")

        if job.properties['status'] == JobStatus.FAILED:
            LOGGER.error("Job finished with errors.")
            return
        LOGGER.info("Job finished with success. Staging out the results...")
        self.stage_out_results(job)
        LOGGER.info("Finished execution.")

    def stage_out_results(self, job):
        content = job.working_dir.listdir()

        storage_config_file = content.get(self.file_name)
        if storage_config_file is None:
            LOGGER.info(f"Could not find file: {self.file_name}")
            LOGGER.info("Could not finalize the stage out. "
                        "Please download your results manually using the 'PyUnicore Tasks Stream' tool.")
        else:
            storage_config_file.download(self.file_name)
            LOGGER.info(f"{self.file_name} file has been downloaded successfully.")

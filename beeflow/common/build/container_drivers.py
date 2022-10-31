"""Container build driver.

All container-based build systems belong here.
"""

import os
import shutil
import subprocess
import tempfile
from beeflow.common.config_driver import BeeConfig as bc
from beeflow.common import log as bee_logging
from beeflow.common.build.build_driver import BuildDriver
from beeflow.common.crt.charliecloud_driver import CharliecloudDriver as crt_driver


log = bee_logging.setup(__name__)


class ContainerBuildDriver(BuildDriver):
    """Driver interface between WFM and a container build system.

    A driver object must implement an __init__ method that
    requests a RTE, and a method to return the requested RTE.
    """


class CharliecloudBuildDriver(ContainerBuildDriver):
    """Driver interface between WFM and a container build system.

    A driver object must implement an __init__ method that
    requests a RTE, and a method to return the requested RTE.
    """

    def __init__(self, task):
        """Begin build request.

        Parse hints and requirements to determine target build
        system. Harvest relevant BeeConfig params in kwargs.

        :param requirements: the workflow requirements
        :type requirements: set of Requirement instances
        :param hints: the workflow hints (optional requirements)
        :type hints: set of Requirement instances
        :param kwargs: Dictionary of build system config options
        :type kwargs: set of build system parameters
        """
        # Store build container archive pased on config file or relative to bee_workdir if not set.
        container_archive = bc.get('builder', 'container_archive')
        self.container_archive = bc.resolve_path(container_archive)
        os.makedirs(self.container_archive, exist_ok=True)
        # Deploy build tarballs relative to /var/tmp/username/beeflow by default
        deployed_image_root = bc.get('builder', 'deployed_image_root')
        # Make sure conf_file path exists
        os.makedirs(deployed_image_root, exist_ok=True)
        # Make sure path is absolute
        deployed_image_root = bc.resolve_path(deployed_image_root)
        self.deployed_image_root = deployed_image_root
        os.makedirs(self.deployed_image_root, exist_ok=True)
        # Set container-relative output directory based on BeeConfig, or use '/'
        container_output_path = bc.get('builder', 'container_output_path')
        self.container_output_path = container_output_path
        # record that a Charliecloud builder was used
        # bc.modify_section('user', 'builder', {'container_type': 'charliecloud'})
        self.task = task
        self.docker_image_id = None
        self.container_name = None
        docker_requirements = set()
        try:
            requirement_docker_requirements = self.task.requirements['DockerRequirement'].keys()
            docker_requirements = docker_requirements.union(requirement_docker_requirements)
            req_string = (f'{set(requirement_docker_requirements)}')
            log.info(f'task {self.task.id} requirement DockerRequirements: {req_string}')
        except (TypeError, KeyError):
            log.info(f'task {self.task.name} {self.task.id} no DockerRequirements in requirement')
        try:
            hint_docker_requirements = self.task.hints['DockerRequirement'].keys()
            docker_requirements = docker_requirements.union(hint_docker_requirements)
            hint_str = (f'{set(hint_docker_requirements)}')
            log.info(f'task {self.task.name} {self.task.id} hint DockerRequirements: {hint_str}')
        except (TypeError, KeyError):
            log.info(f'task {self.task.name} {self.task.id} hints has no DockerRequirements')
        log.info(f'task {self.task.id} union DockerRequirements : {docker_requirements}')
        exec_superset = self.resolve_priority()
        self.exec_list = [i for i in exec_superset if i[1] in docker_requirements]
        log_exec_list = [i[1] for i in self.exec_list]
        log.info(f'task {self.task.id} DockerRequirement execution order will be: {log_exec_list}')
        log.info('Execution order pre-empts hint/requirement status.')

    def get_docker_req(self, docker_req_param):
        """Get dockerRequirement, prioritizing requirements over hints.

        :param docker_req_param: the dockerRequirement parameter (e.g. 'dockerFile')
        :type docker_req_param: str

        When requirements are specified hints will be ignored.
        By default, tasks need not specify hints or requirements
        """
        task_docker_req = None
        # Get value if specified in requirements
        try:
            # Try to get Requirements
            task_docker_req = self.task.requirements['DockerRequirement'][docker_req_param]
        except (KeyError, TypeError):
            # Task Requirements are not mandatory. No docker_req_param specified in task reqs.
            task_docker_req = None
        # Ignore hints if requirements available
        if not task_docker_req:
            # Get value if specified in hints
            try:
                # Try to get Hints
                task_docker_req = self.task.hints['DockerRequirement'][docker_req_param]
            except (KeyError, TypeError):
                # Task Hints are not mandatory. No docker_req_param specified in task hints.
                task_docker_req = None
        return task_docker_req

    def process_docker_pull(self, addr=None, force=False):
        """Get the CWL compliant dockerPull dockerRequirement.

        CWL spec 09-23-2020: Specify a Docker image to
        retrieve using docker pull. Can contain the immutable
        digest to ensure an exact container is used.
        """
        task_addr = self.get_docker_req('dockerPull')

        # Use task specified image if image parameter empty
        if not addr:
            addr = task_addr

        # If Requirement is set but not specified, and param empty, do nothing and error.
        if self.task.requirements == {} and not addr:
            log.error("dockerPull set but no image path specified.")
            return 1
        # If no image specified and no image required, nothing to do.
        if not task_addr and not addr:
            log.info('No image specified and no image required, nothing to do.')
            return 0

        # Determine name for successful build target
        ch_build_addr = addr.replace('/', '%')

        ch_build_target = '/'.join([self.container_archive, ch_build_addr]) + '.tar.gz'
        # Return if image already exist and force==False.
        if os.path.exists(ch_build_target) and not force:
            log.info('Image already exists. If you want to refresh container, use force option.')
            log.info(f'Image path: {ch_build_target}')
            return 0
        # Force remove any cached images if force==True
        if os.path.exists(ch_build_target) and force:
            try:
                os.remove(ch_build_target)
            except FileNotFoundError:
                pass
            try:
                shutil.rmtree('/var/tmp/' + os.getlogin() + '/ch-image/' + ch_build_addr)
            except FileNotFoundError:
                pass

        # Out of excuses. Pull the image.
        cmd = (f'ch-image pull {addr}\n'
               f'ch-convert -i ch-image -o tar {ch_build_addr}'
               f' {self.container_archive}/{ch_build_addr}.tar.gz'
               )
        return subprocess.run(cmd, check=True, shell=True)

    def process_docker_load(self):
        """Get and process the CWL compliant dockerLoad dockerRequirment.

        CWL spec 09-23-2020: Specify a HTTP URL from which to
        download a Docker image using docker load.
        """
        # Need to know if dockerLoad is specified in order to determine fail/success
        req_dockerload = self.get_docker_req('dockerLoad')
        log.warning('Charliecloud does not have the concept of a layered image tarball.')
        log.warning('Did you mean to use dockerImport?')
        if req_dockerload:
            log.warning('dockerLoad specified as requirement.')
            return 1
        return 0

    def process_docker_file(self, task_dockerfile=None, force=False):
        """Get and process the CWL compliant dockerFile dockerRequirement.

        CWL spec 09-23-2020: Supply the contents of a Dockerfile
        which will be built using docker build. We have discussed implementing CWL
        change to expect a file handle instead of file contents, and use the file
        handle expectation here.
        """
        # beeflow:containerName is always processed before dockerFile, so safe to assume it exists
        # otherwise, raise an error.
        if self.container_name is None:
            log.error("dockerFile may not be specified without beeflow:containerName")
            return 1

        # Need dockerfile in order to build, else fail
        task_dockerfile = self.get_docker_req('dockerFile')
        if not task_dockerfile:
            log.error("dockerFile not specified as task attribute or parameter.")
            return 1

        # Create context directory to use as Dockerfile context, use container name so user
        # can prep the directory with COPY sources as needed.
        context_dir = os.path.expanduser('~')
        log.info(f'Context directory will be {context_dir}')

        # Determine name for successful build target
        ch_build_addr = self.container_name.replace('/', '%')

        ch_build_target = '/'.join([self.container_archive, ch_build_addr]) + '.tar.gz'
        log.info(f'Build will create tar ball at {ch_build_target}')
        # Return if image already exist and force==False.
        if os.path.exists(ch_build_target) and not force:
            return 0
        # Force remove any cached images if force==True
        if os.path.exists(ch_build_target) and force:
            try:
                os.remove(ch_build_target)
            except FileNotFoundError:
                pass
            try:
                shutil.rmtree('/var/tmp/' + os.getlogin() + '/ch-image/' + ch_build_addr)
            except FileNotFoundError:
                pass

        # Out of excuses. Build the image.
        with tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8') as tmp:
            # Write the dockerfile to the tempfile
            tmp.write(task_dockerfile)
            tmp.flush()
            dockerfile_path = tmp.name
            # Build and run the command
            log.info('Context directory configured. Beginning build.')
            cmd = (f'ch-image build -t {self.container_name} --force '
                   f'-f {dockerfile_path} {context_dir}\n'
                   f'ch-convert -i ch-image -o tar {ch_build_addr} '
                   f'{self.container_archive}/{ch_build_addr}.tar.gz'
                   )
            log.info(f'Executing: {cmd}')
            return subprocess.run(cmd, check=True, shell=True)

    def process_docker_import(self, param_import=None):
        """Get and process the CWL compliant dockerImport dockerRequirement.

        CWL spec 09-23-2020: Provide HTTP URL to download and
        gunzip a Docker images using docker import. The param_import
        may be used to override DockerReuirement specs.
        """
        # If parameter import is specified, use that, otherwise look at task.
        if param_import:
            import_input_path = param_import
        else:
            # Get path for tarball to import
            import_input_path = self.get_docker_req('dockerImport')

        # Pull the image.
        file_name = crt_driver.get_ccname(import_input_path)
        cmd = (f'ch-convert {import_input_path} {self.deployed_image_root}/{file_name}')
        log.info(f'Docker import: Assuming container name is {import_input_path}. Correct?')
        return subprocess.run(cmd, check=True, shell=True)

    def process_docker_image_id(self, param_imageid=None):
        """Get and process the CWL compliant dockerImageId dockerRequirement.

        A divergence from the CWL spec. Docker image Id is defined by docker as a checksum
        on a container, not a human-readable name. The Docker image ID must be produced after
        the container is built, and can not be used to tag the container for that reason.
        The param_imageid may be used to override DockerRequirement specs.
        """
        # Parameter takes precedence
        if param_imageid:
            self.docker_image_id = param_imageid
        # If previously set by param, return 0 and ignore task.
        if self.docker_image_id:
            return 0

        # Need ImageId to know how dockerFile should be named, else fail
        task_image_id = self.get_docker_req('dockerImageId')

        # Set imageid
        self.docker_image_id = task_image_id

        # If task and parameter still doesn't specify ImageId, consider this an error.
        if not self.docker_image_id:
            return 0
        return 1

    def process_docker_output_directory(self, param_output_directory=None):
        """Get and process the CWL compliant dockerOutputDirectory dockerRequirement.

        CWL spec 09-23-2020: Set the designated output directory
        to a specific location inside the Docker container. The
        param_output_directory may be used to override DockerRequirement
        specs.
        """
        # Allow parameter over-ride.
        if param_output_directory:
            self.container_output_path = param_output_directory
        return 0

    def process_copy_container(self, force=False):
        """Get and process the BEE CWL extension copyContainer dockerRequirement.

        This CWL extension will copy an existing container to the build archive.

        If you have a container tarball, and all you need to do is stage it,
        that is, all you need to do is copy it to a location that BEE knows,
        use this to put the container into the build archive.
        """
        # Need container_path to know how dockerfile should be named, else fail
        task_container_path = self.get_docker_req('beeflow:copyContainer')
        if not task_container_path:
            log.error("beeflow:copyContainer: You must specify the path to an existing container.")
            return 1

        if self.container_name:
            copy_target = '/'.join([self.container_archive, self.container_name + '.tar.gz'])
        else:
            copy_target = '/'.join([self.container_archive,
                                    crt_driver.get_ccname(task_container_path) + '.tar.gz'])
        log.info(f'Build will copy a container to {copy_target}')
        # Return if image already exist and force==False.
        if os.path.exists(copy_target) and not force:
            log.info('Container by this name exists in archive. Taking no action.')
            return 0
        # Force remove any cached images if force==True
        if os.path.exists(copy_target) and force:
            try:
                os.remove(copy_target)
            except FileNotFoundError:
                pass

        log.info('Copying container.')
        cmd = (f'cp {task_container_path} {copy_target}\n'
               )
        log.info(f'Executing: {cmd}')
        return subprocess.run(cmd, check=True, shell=True)

    def process_container_name(self):
        """Get and process BEE CWL extension for containerName dockerRequirement.

        This is a BEE extension to CWL to refer to containers with human-readable name.

        The CWL spec currently uses dockerImageId to refer to the name of a container
        but this is explicitly not how Docker defines it. We need a way to name
        containers in a human readable format.
        """
        task_container_name = self.get_docker_req('beeflow:containerName')
        if not task_container_name and self.docker_image_id is None:
            log.error("beeflow:containerName: You must specify the containerName or dockerImageId")
            return 1
        self.container_name = task_container_name
        log.info(f'Setting container_name to: {self.container_name}')
        return 0


class SingularityBuildDriver(ContainerBuildDriver):
    """Driver interface between WFM and a container build system.

    A driver object must implement an __init__ method that
    requests a RTE, and a method to return the requested RTE.
    """

    def __init__(self, task, userconf_file=None):
        """Begin build request.

        Parse hints and requirements to determine target build
        system. Harvest relevant BeeConfig params in kwargs.

        :param requirements: the workflow requirements
        :type requirements: set of Requirement instances
        :param hints: the workflow hints (optional requirements)
        :type hints: set of Requirement instances
        :param kwargs: Dictionary of build system config options
        :type kwargs: set of build system parameters
        """

    def process_docker_pull(self, addr=None, force=False):
        """Get and process the CWL compliant dockerPull dockerRequirement.

        CWL spec 09-23-2020: Specify a Docker image to
        retrieve using docker pull. Can contain the immutable
        digest to ensure an exact container is used.
        """

    def process_docker_load(self):
        """Get and process the CWL compliant dockerLoad dockerRequirement.

        CWL spec 09-23-2020: Specify a HTTP URL from which to
        download a Docker image using docker load.
        """

    def process_docker_file(self, task_dockerfile=None, force=False):
        """Get and process the CWL compliant dockerFile dockerRequirement.

        CWL spec 09-23-2020: Supply the contents of a Dockerfile
        which will be built using docker build.
        """

    def process_docker_import(self, param_import=None):
        """Get and process the CWL compliant dockerImport dockerRequirement.

        CWL spec 09-23-2020: Provide HTTP URL to download and
        gunzip a Docker images using docker import. The param_import
        may be used to override DockerRequirement specs.
        """

    def process_docker_image_id(self, param_imageid=None):
        """Get and process the CWL compliant dockerImageId dockerRequirement.

        CWL spec 09-23-2020: The image id that will be used for
        docker run. May be a human-readable image name or the
        image identifier hash. May be skipped if dockerPull is
        specified, in which case the dockerPull image id must be
        used. The param_imageid may be used to override DockerRequirement
        specs.
        """

    def process_docker_output_directory(self, param_output_directory=None):
        """Get and process the CWL compliant dockerOutputDirectory.

        CWL spec 09-23-2020: Set the designated output directory
        to a specific location inside the Docker container. The
        param_output_directory may be used to override DockerRequirement
        specs.
        """
# Ignore W0231: linter doesn't know about abstract classes, it's ok to now call the parent __init__
# pylama:ignore=W0231

"""Container build driver.

All container-based build systems belong here.
"""

from abc import ABC
import os
import tempfile
import shutil
import subprocess
from beeflow.common.config.config_driver import BeeConfig
# from beeflow.common.crt.crt_drivers import CharliecloudDriver, SingularityDriver


class ContainerBuildDriver(ABC):
    """Driver interface between WFM and a container build system.

    A driver object must implement an __init__ method that
    requests a RTE, and a method to return the requested RTE.
    """


class CharliecloudBuildDriver(ContainerBuildDriver):
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
        if userconf_file:
            bc = BeeConfig(userconfig=userconf_file)
        else:
            bc = BeeConfig()
        # Store build tarballs relative to bee_workdir.
        try:
            if bc.userconfig['DEFAULT'].get('bee_workdir'):
                build_dir = '/'.join([bc.userconfig['DEFAULT'].get('bee_workdir'),
                                     'build_cache'])
            else:
                print('Invalid config file. bee_workdir not found in DEFAULT.')
                print('Assuming bee_workdir is ~/.beeflow')
                build_dir = '~/.beeflow/build_cache'
        except KeyError:
            print('Invalid config file. DEFAULT section missing.')
            print('Assuming bee_workdir is ~/.beeflow')
            build_dir = '~/.beeflow/build_cache'
        finally:
            self.build_dir = bc.resolve_path(build_dir)
            os.makedirs(self.build_dir, exist_ok=True)
            print('Build cache directory is:', self.build_dir)
        # Deploy build tarballs relative to /var/tmp/username/beeflow by default
        try:
            if bc.userconfig['builder'].get('deployed_image_root'):
                deployed_image_root = bc.userconfig['builder'].get('deployed_image_root')
                # Make sure conf_file path exists
                os.makedirs(deployed_image_root, exist_ok=True)
                # Make sure path is absolute
                deployed_image_root = bc.resolve_path(deployed_image_root)
            else:
                print('Deployed image root not found.')
                deployed_image_root = '/'.join(['/var/tmp', os.getlogin(), 'beeflow'])
                # Make sure conf_file path exists
                os.makedirs(deployed_image_root, exist_ok=True)
                # Make sure path is absolute
                deployed_image_root = bc.resolve_path(deployed_image_root)
                print(f'Assuming deployed image root is {deployed_image_root}')
        except KeyError:
            print('Config file is missing builder section.')
            deployed_image_root = '/'.join(['/var/tmp', os.getlogin(), 'beeflow'])
            # Make sure conf_file path exists
            os.makedirs(deployed_image_root, exist_ok=True)
            # Make sure path is absolute
            deployed_image_root = bc.resolve_path(deployed_image_root)
            print(f'Assuming deployed image root is {deployed_image_root}')
            bc.modify_section('user', 'builder', {'deployed_image_root': deployed_image_root})
            print("Wrote deployed image root to user BeeConfig file.")
        finally:
            self.deployed_image_root = deployed_image_root
            os.makedirs(self.deployed_image_root, exist_ok=True)
            print('Deployed image root directory is:', self.deployed_image_root)
        self.task = task
        self.docker_image_id = None

    def parse_build_config(self):
        """Parse bc_options to separate BeeConfig and CWL concerns.

        bc_options is used to receive an unknown number of parameters.
        both BeeConfig and CWL files may have options required for
        the build service. Parse and store them.
        """
        print('Charliecloud, parse_build_config:', self, '.')

    def validate_build_config(self):
        """Ensure valid config.

        Parse bc_options to ensure BeeConfig options are compatible
        with CWL specs.
        """
        print('Charliecloud, validate_build_config:', self, '.')

    def build(self):
        """Build RTE as configured.

        Build the RTE based on a validated configuration.
        """
        print('Charliecloud, validate_build_config:', self, '.')

    def validate_build(self):
        """Validate RTE.

        Confirm build procedure completed successfully.
        """
        print('Charliecloud, validate_build:', self, '.')

    def dockerPull(self, addr=None, force=False):
        """CWL compliant dockerPull.

        CWL spec 09-23-2020: Specify a Docker image to
        retrieve using docker pull. Can contain the immutable
        digest to ensure an exact container is used.
        """
        # By default, tasks need not specify hints or reqs
        task_addr = None
        try:
            # Try to get Hints
            hint_addr = self.task.hints['DockerRequirement']['dockerPull']
        except (KeyError, TypeError):
            # Task Hints are not mandatory. No dockerPull image specified in task hints.
            hint_addr = None
        try:
            # Try to get Requirements
            req_addr = self.task.requirements['DockerRequirement']['dockerPull']
        except (KeyError, TypeError):
            # Task Requirements are not mandatory. No dockerPull image specified in task reqs.
            req_addr = None

        # Prefer requirements over hints
        if (req_addr or hint_addr) and (not hint_addr):
            task_addr = req_addr
        elif hint_addr:
            task_addr = hint_addr

        # Use task specified image if image parameter empty
        if not addr:
            addr = task_addr

        # If Requirement is set but not specified, and param empty, do nothing and error.
        if self.task.requirements == {} and not addr:
            print("ERROR: dockerPull set but no image path specified.")
            return 1
        # If no image specified and no image required, nothing to do.
        if not req_addr and not addr:
            return 0

        # DetermVine name for successful build target
        ch_build_addr = addr.replace('/', '%')

        ch_build_target = '/'.join([self.build_dir, ch_build_addr]) + '.tar.gz'
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
                shutil.rmtree('/var/tmp/'+os.getlogin()+'/ch-grow/'+ch_build_addr)
            except FileNotFoundError:
                pass

        # Provably out of excuses. Pull the image.
        cmd = (f'ch-grow pull {addr}\n'
               f'ch-builder2tar {ch_build_addr} {self.build_dir}'
               )
        return subprocess.run(cmd, capture_output=True, check=True, shell=True)

    def dockerLoad(self):
        """CWL compliant dockerLoad.

        CWL spec 09-23-2020: Specify a HTTP URL from which to
        download a Docker image using docker load.
        """

    def dockerFile(self, task_imageid=None, task_dockerfile=None, force=False):
        """CWL compliant dockerFile.

        CWL spec 09-23-2020: Supply the contents of a Dockerfile
        which will be built using docker build.
        """
        # Need imageid to know how dockerfile should be named, else fail
        try:
            # Try to get Hints
            hint_imageid = self.task.hints['DockerRequirement']['dockerImageId']
        except (KeyError, TypeError):
            # Task Hints are not mandatory. No imageid specified in task hints.
            hint_imageid = None
        try:
            # Try to get Requirements
            req_imageid = self.task.requirements['DockerRequirement']['dockerImageId']
        except (KeyError, TypeError):
            # Task Requirements are not mandatory. No imageid specified in task reqs.
            req_imageid = None

        # Prefer requirements over hints
        if (req_imageid or hint_imageid) and (not hint_imageid):
            task_imageid = req_imageid
        elif hint_imageid:
            task_imageid = hint_imageid

        if not task_imageid:
            print("ERROR: dockerFile may not be specified without dockerImageId")
            return 1

        # Need dockerfile in order to build, else fail
        try:
            # Try to get Hints
            hint_dockerfile = self.task.hints['DockerRequirement']['dockerFile']
        except (KeyError, TypeError):
            # Task Hints are not mandatory. No dockerfile specified in task hints.
            hint_dockerfile = None
        try:
            # Try to get Requirements
            req_dockerfile = self.task.requirements['DockerRequirement']['dockerFile']
        except (KeyError, TypeError):
            # Task Requirements are not mandatory. No dockerfile specified in task reqs.
            req_dockerfile = None

        # Prefer requirements over hints
        if (req_dockerfile or hint_dockerfile) and (not hint_dockerfile):
            task_dockerfile = req_dockerfile
        elif hint_dockerfile:
            task_dockerfile = hint_dockerfile

        if not task_dockerfile:
            print("ERROR: dockerFile not specified as task attribute or parameter.")
            return 1

        # Create random directory to use as Dockerfile context
        tmp_dir = tempfile.mkdtemp(prefix=f'bee_task{self.task.name}_id{self.task.id}", dir="/tmp')
        tmp_dockerfile = f'{tmp_dir}/Dockerfile'
        # Now that we know what the image is called, make a Dockerfile for CCloud
        with open(tmp_dockerfile, 'w') as fh:
            fh.write(task_dockerfile)

        # Determine name for successful build target
        ch_build_addr = task_imageid.replace('/', '%')

        ch_build_target = '/'.join([self.build_dir, ch_build_addr]) + '.tar.gz'
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
                shutil.rmtree('/var/tmp/'+os.getlogin()+'/ch-grow/'+ch_build_addr)
            except FileNotFoundError:
                pass

        # Provably out of excuses. Pull the image.
        cmd = (f'ch-grow build -t {task_imageid} -f {tmp_dockerfile} {tmp_dir}\n'
               f'ch-builder2tar {ch_build_addr} {self.build_dir}'
               )
        return subprocess.run(cmd, capture_output=True, check=True, shell=True)

    def dockerImport(self, param_import=None):
        """CWL compliant dockerImport.

        CWL spec 09-23-2020: Provide HTTP URL to download and
        gunzip a Docker images using docker import.
        """
        # If parameter import is specified, use that, otherwise look at task.
        if param_import:
            import_input_path = param_import
        else:
            # Get path for tarball to import
            try:
                # Try to get Hints
                hint_import = self.task.hints['DockerRequirement']['dockerImport']
            except (KeyError, TypeError):
                # Task Hints are not mandatory. No import specified in task hints.
                hint_import = None
            try:
                # Try to get Requirements
                req_import = self.task.requirements['DockerRequirement']['dockerImport']
            except (KeyError, TypeError):
                # Task Requirements are not mandatory. No import specified in task reqs.
                req_import = None
            # Prefer requirements over hints
            if (req_import or hint_import) and (not hint_import):
                task_import = req_import
            elif hint_import:
                task_import = hint_import
            # Set import
            import_input_path = task_import

        # Pull the image.
        cmd = (f'ch-tar2dir {import_input_path} {self.deployed_image_root}/')
        return subprocess.run(cmd, capture_output=True, check=True, shell=True)

    def dockerImageId(self, param_imageid=None):
        """CWL compliant dockerImageId.

        CWL spec 09-23-2020: The image id that will be used for
        docker run. May be a human-readable image name or the
        image identifier hash. May be skipped if dockerPull is
        specified, in which case the dockerPull image id must be
        used.
        """
        if param_imageid:
            self.docker_image_id = param_imageid
            return 0

        # Need imageid to know how dockerfile should be named, else fail
        try:
            # Try to get Hints
            hint_imageid = self.task.hints['DockerRequirement']['dockerImageId']
        except (KeyError, TypeError):
            # Task Hints are not mandatory. No imageid specified in task hints.
            hint_imageid = None
        try:
            # Try to get Requirements
            req_imageid = self.task.requirements['DockerRequirement']['dockerImageId']
        except (KeyError, TypeError):
            # Task Requirements are not mandatory. No imageid specified in task reqs.
            req_imageid = None

        # Prefer requirements over hints
        if (req_imageid or hint_imageid) and (not hint_imageid):
            task_imageid = req_imageid
        elif hint_imageid:
            task_imageid = hint_imageid

        # Set imageid
        self.docker_image_id = task_imageid

        # If task and parameter still doesn't specify image_id, consider this an error.
        if self.docker_image_id:
            return 0
        return 1

    def dockerOutputDirectory(self):
        """CWL compliant dockerOutputDirectory.

        CWL spec 09-23-2020: Set the designated output directory
        to a specific location inside the Docker container.
        """


class SingularityBuildDriver(ContainerBuildDriver):
    """Driver interface between WFM and a container build system.

    A driver object must implement an __init__ method that
    requests a RTE, and a method to return the requested RTE.
    """

    def initialize_builder(self, requirements, hints, bc_options):
        """Begin build request.

        Parse hints and requirements to determine target build
        system. Harvest relevant BeeConfig params in bc_options.

        :param requirements: the workflow requirements
        :type requirements: set of Requirement instances
        :param hints: the workflow hints (optional requirements)
        :type hints: set of Requirement instances
        :param bc_options: Dictionary of build system config options
        :type bc_options: set of build system parameters
        """
        print('Singularity, initialize_builder:', self, requirements, hints, bc_options, '.')

    def parse_build_config(self):
        """Parse bc_options to separate BeeConfig and CWL concerns.

        bc_options is used to receive an unknown number of parameters.
        both BeeConfig and CWL files may have options required for
        the build service. Parse and store them.
        """
        print('Singularity, parse_build_config:', self, '.')

    def validate_build_config(self):
        """Ensure valid config.

        Parse bc_options to ensure BeeConfig options are compatible
        with CWL specs.
        """
        print('Singularity, validate_build_config:', self, '.')

    def build(self):
        """Build RTE as configured.

        Build the RTE based on a validated configuration.
        """
        print('Singularity, validate_build_config:', self, '.')

    def validate_build(self):
        """Validate RTE.

        Confirm build procedure completed successfully.
        """
        print('Singularity, validate_build:', self, '.')

    def dockerPull(self):
        """CWL compliant dockerPull.

        CWL spec 09-23-2020: Specify a Docker image to
        retrieve using docker pull. Can contain the immutable
        digest to ensure an exact container is used.
        """

    def dockerLoad(self):
        """CWL compliant dockerLoad.

        CWL spec 09-23-2020: Specify a HTTP URL from which to
        download a Docker image using docker load.
        """

    def dockerFile(self):
        """CWL compliant dockerFile.

        CWL spec 09-23-2020: Supply the contents of a Dockerfile
        which will be built using docker build.
        """

    def dockerImport(self):
        """CWL compliant dockerImport.

        CWL spec 09-23-2020: Provide HTTP URL to download and
        gunzip a Docker images using docker import.
        """

    def dockerImageId(self):
        """CWL compliant dockerImageId.

        CWL spec 09-23-2020: The image id that will be used for
        docker run. May be a human-readable image name or the
        image identifier hash. May be skipped if dockerPull is
        specified, in which case the dockerPull image id must be
        used.
        """

    def dockerOutputDirectory(self):
        """CWL compliant dockerOutputDirectory.

        CWL spec 09-23-2020: Set the designated output directory
        to a specific location inside the Docker container.
        """
# Ignore snake_case requirement to enable CWL compliant names.
# pylama:ignore=C0103

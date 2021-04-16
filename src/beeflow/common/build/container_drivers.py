"""Container build driver.

All container-based build systems belong here.
"""

from abc import ABC
import os
import tempfile
import shutil
import subprocess
from beeflow.common.config_driver import BeeConfig
import sys
# from beeflow.common.crt.crt_drivers import CharliecloudDriver, SingularityDriver
from beeflow.cli import log
from beeflow.common.build.build_driver import BuildDriver
import beeflow.common.log as bee_logging


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
                bee_workdir = bc.userconfig['DEFAULT'].get('bee_workdir')
                build_dir = '/'.join([bee_workdir,'build_cache'])
                handler = bee_logging.save_log(bee_workdir=bee_workdir, log=log,
                                              logfile='CharliecloudBuildDriver.log')
            else:
                # Can't log if we don't know where to log, just print error
                print('Invalid config file. bee_workdir not found in DEFAULT.', file=sys.stderr)
                print('Assuming bee_workdir is ~/.beeflow', file=sys.stderr)
                build_dir = '~/.beeflow/build_cache'
        except KeyError:
            # Can't log if we don't know where to log, just print error
            print('Invalid config file. DEFAULT section missing.', file=sys.stderr)
            print('Assuming bee_workdir is ~/.beeflow', file=sys.stderr)
            build_dir = '~/.beeflow/build_cache'
        finally:
            self.build_dir = bc.resolve_path(build_dir)
            os.makedirs(self.build_dir, exist_ok=True)
            log.info(f'Build cache directory is: {self.build_dir}')
        # Deploy build tarballs relative to /var/tmp/username/beeflow by default
        try:
            if bc.userconfig['builder'].get('deployed_image_root'):
                deployed_image_root = bc.userconfig['builder'].get('deployed_image_root')
                # Make sure conf_file path exists
                os.makedirs(deployed_image_root, exist_ok=True)
                # Make sure path is absolute
                deployed_image_root = bc.resolve_path(deployed_image_root)
            else:
                log.info('Deployed image root not found.')
                deployed_image_root = '/'.join(['/var/tmp', os.getlogin(), 'beeflow'])
                # Make sure conf_file path exists
                os.makedirs(deployed_image_root, exist_ok=True)
                # Make sure path is absolute
                deployed_image_root = bc.resolve_path(deployed_image_root)
                log.info(f'Assuming deployed image root is {deployed_image_root}')
        except KeyError:
            log.info('Config file is missing builder section.')
            deployed_image_root = '/'.join(['/var/tmp', os.getlogin(), 'beeflow'])
            # Make sure conf_file path exists
            os.makedirs(deployed_image_root, exist_ok=True)
            # Make sure path is absolute
            deployed_image_root = bc.resolve_path(deployed_image_root)
            log.info(f'Assuming deployed image root is {deployed_image_root}')
            bc.modify_section('user', 'builder', {'deployed_image_root': deployed_image_root})
            log.info("Wrote deployed image root to user BeeConfig file.")
        finally:
            self.deployed_image_root = deployed_image_root
            os.makedirs(self.deployed_image_root, exist_ok=True)
            log.info(f'Deployed image root directory is: {self.deployed_image_root}')
        # Set container-relative output directory based on BeeConfig, or use '/'
        try:
            container_output_path = bc.userconfig['builder'].get('container_output_path')
            # If the builder section exists but not the container_output_path entry,
            # bc will return "None". Treat this is as a KeyError.
            if not container_output_path:
                raise KeyError
        except KeyError:
            container_output_path = '/'
            log.info(f'Assuming container-relative output path is {container_output_path}')
            bc.modify_section('user', 'builder', {'container_output_path': container_output_path})
            log.info('Wrote container-relative output path to user BeeConfig file.')
        finally:
            self.container_output_path = container_output_path
            log.info(f'Container-relative output path is: {self.container_output_path}')
        # record that a Charliecloud builder was used
        bc.modify_section('user', 'builder', {'container_type':'charliecloud'})
        self.task = task
        self.docker_image_id = None
        print('task stuff')
        dockerRequirements = set() 
        try:
            requirement_DockerRequirements = self.task.requirements['DockerRequirement'].keys()
            dockerRequirements = dockerRequirements.union(requirement_DockerRequirements)
            log.info('task {} requirement DockerRequirements: {}'.\
                     format(self.task.id, set(requirement_DockerRequirements)))
        except TypeError:
            log.info('task {} requirements has no DockerRequirements'.format(self.task.id))
            pass
        try:
            hint_DockerRequirements = self.task.hints['DockerRequirement'].keys()
            dockerRequirements = dockerRequirements.union(hint_DockerRequirements)
            log.info('task {} hint DockerRequirements: {}'.format(self.task.id,
                                                                  set(hint_DockerRequirements)))
        except TypeError:
            log.info('task {} hints has no DockerRequirements'.format(self.task.id))
            pass
        log.info('task {} union DockerRequirements consist of: {}'.format(self.task.id,
                                                                          dockerRequirements))
        exec_superset = self.resolve_priority()
        self.exec_list = [i for i in exec_superset if i[1] in dockerRequirements]
        log_exec_list = [i[1] for i in self.exec_list]
        log.info('task {} DockerRequirement execution order will be: {}'.format(self.task.id,
                                                                                log_exec_list))
        log.info('Execution order pre-empts hint/requirement status.')

    def parse_build_config(self):
        """Parse bc_options to separate BeeConfig and CWL concerns.

        bc_options is used to receive an unknown number of parameters.
        both BeeConfig and CWL files may have options required for
        the build service. Parse and store them.
        """
        log.info('Charliecloud, parse_build_config:', self, '.')

    def validate_build_config(self):
        """Ensure valid config.

        Parse bc_options to ensure BeeConfig options are compatible
        with CWL specs.
        """
        log.info('Charliecloud, validate_build_config:', self, '.')

    def build(self):
        """Build RTE as configured.

        Build the RTE based on a validated configuration.
        """
        log.info('Charliecloud, validate_build_config:', self, '.')

    def validate_build(self):
        """Validate RTE.

        Confirm build procedure completed successfully.
        """
        log.info('Charliecloud, validate_build:', self, '.')

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
            log.error("dockerPull set but no image path specified.")
            return 1
        # If no image specified and no image required, nothing to do.
        if not req_addr and not addr:
            log.info('No image specified and no image required, nothing to do.')
            return 0

        # DetermVine name for successful build target
        ch_build_addr = addr.replace('/', '%')

        ch_build_target = '/'.join([self.build_dir, ch_build_addr]) + '.tar.gz'
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
                shutil.rmtree('/var/tmp/'+os.getlogin()+'/ch-image/'+ch_build_addr)
            except FileNotFoundError:
                pass

        # Provably out of excuses. Pull the image.
        cmd = (f'ch-image pull {addr} && ch-builder2tar {ch_build_addr} {self.build_dir}'
               )
        return subprocess.run(cmd, capture_output=True, check=True, shell=True)

    def dockerLoad(self):
        """CWL compliant dockerLoad.

        CWL spec 09-23-2020: Specify a HTTP URL from which to
        download a Docker image using docker load.
        """
        # Need to know if dockerLoad is a requirement in order to determine fail/success
        try:
            # Try to get Requirements
            req_dockerload = self.task.requirements['DockerRequirement']['dockerLoad']
        except (KeyError, TypeError):
            # Task Requirements are not mandatory. No dockerload specified in task reqs.
            req_dockerload = None

        log.error('Charliecloud does not have the concept of a layered image tarball.')
        log.error('Did you mean to use dockerImport?')
        if req_dockerload:
            log.error('dockerLoad specified as requirement.')
            return 1
        return 0

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
            log.error("dockerFile may not be specified without dockerImageId")
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
            log.error("dockerFile not specified as task attribute or parameter.")
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
                shutil.rmtree('/var/tmp/'+os.getlogin()+'/ch-image/'+ch_build_addr)
            except FileNotFoundError:
                pass

        # Provably out of excuses. Pull the image.
        cmd = (f'ch-image build -t {task_imageid} -f {tmp_dockerfile} {tmp_dir}\n'
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
        # Parameter takes precedence
        if param_imageid:
            self.docker_image_id = param_imageid
        # If previously set by param, return previous setting and ignore task.
        if self.docker_image_id:
            return self.docker_image_id

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
        task_imageid = None
        if (req_imageid or hint_imageid) and (not hint_imageid):
            task_imageid = req_imageid
        elif hint_imageid:
            task_imageid = hint_imageid

        # Set imageid
        self.docker_image_id = task_imageid

        # If task and parameter still doesn't specify image_id, consider this an error.
        if self.docker_image_id:
            return self.docker_image_id
        return 1

    def dockerOutputDirectory(self, param_output_directory=None):
        """CWL compliant dockerOutputDirectory.

        CWL spec 09-23-2020: Set the designated output directory
        to a specific location inside the Docker container.
        """
        # Allow parameter over-ride.
        if param_output_directory:
            self.container_output_path = param_output_directory
        return self.container_output_path


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
        log.info('Singularity, initialize_builder:', self, requirements, hints, bc_options, '.')

    def parse_build_config(self):
        """Parse bc_options to separate BeeConfig and CWL concerns.

        bc_options is used to receive an unknown number of parameters.
        both BeeConfig and CWL files may have options required for
        the build service. Parse and store them.
        """
        log.info('Singularity, parse_build_config:', self, '.')

    def validate_build_config(self):
        """Ensure valid config.

        Parse bc_options to ensure BeeConfig options are compatible
        with CWL specs.
        """
        log.info('Singularity, validate_build_config:', self, '.')

    def build(self):
        """Build RTE as configured.

        Build the RTE based on a validated configuration.
        """
        log.info('Singularity, validate_build_config:', self, '.')

    def validate_build(self):
        """Validate RTE.

        Confirm build procedure completed successfully.
        """
        log.info('Singularity, validate_build:', self, '.')

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
# Ignore snake_case requirement to enable CWL compliant names. (C0103)
# Ignore "too many statements". Some of these methods are long, and that's ok (R0915)
# pylama:ignore=C0103,R0915

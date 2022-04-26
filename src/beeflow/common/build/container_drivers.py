"""Container build driver.

All container-based build systems belong here.
"""

import os
import shutil
import subprocess
import sys
from beeflow.common.config_driver import BeeConfig
# from beeflow.common.crt.crt_drivers import CharliecloudDriver, SingularityDriver
from beeflow.cli import log
from beeflow.common.build.build_driver import BuildDriver
import beeflow.common.log as bee_logging
from beeflow.common.crt_drivers import CharliecloudDriver as crt_driver


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
        # Store build logs relative to bee_workdir.
        try:
            if bc.userconfig['DEFAULT'].get('bee_workdir'):
                bee_workdir = bc.userconfig['DEFAULT'].get('bee_workdir')
            else:
                # Can't log if we don't know where to log, just print error
                print('Invalid config file. bee_workdir not found in DEFAULT.', file=sys.stderr)
                print('Assuming bee_workdir is ~/.beeflow', file=sys.stderr)
                bee_workdir = '~/.beeflow'
        except KeyError:
            # Can't log if we don't know where to log, just print error
            print('Invalid config file. DEFAULT section missing.', file=sys.stderr)
            print('Assuming bee_workdir is ~/.beeflow', file=sys.stderr)
            bee_workdir = '~/.beeflow'
        finally:
            _ = bee_logging.save_log(bee_workdir=bee_workdir, log=log,
                                     logfile='CharliecloudBuildDriver.log')
        # Store build container archive pased on config file or relative to bee_workdir if not set.
        try:
            if bc.userconfig['builder'].get('container_archive'):
                container_archive = bc.userconfig['builder'].get('container_archive')
            else:
                # Set container archive relative to bee_workdir if config does not specify
                log.warning('Invalid config file. container_archive not found in builder section.')
                container_archive = '/'.join([bee_workdir, 'container_archive'])
                log.warning(f'Assuming container_archive is {container_archive}')
        except KeyError:
            log.warning('Container is missing builder section')
            log.warning('Setting container archive relative to bee_workdir')
            container_archive = f'{bee_workdir}/container_archive'
        finally:
            self.container_archive = bc.resolve_path(container_archive)
            os.makedirs(self.container_archive, exist_ok=True)
            bc.modify_section('user', 'builder', {'container_archive': self.container_archive})
            log.info(f'Build container archive directory is: {self.container_archive}')
            log.info("Wrote deployed image root to user BeeConfig file.")
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
                deployed_image_root = '/'.join(['/var/tmp', os.getlogin(),
                                               'beeflow_deployed_containers'])
                # Make sure conf_file path exists
                os.makedirs(deployed_image_root, exist_ok=True)
                # Make sure path is absolute
                deployed_image_root = bc.resolve_path(deployed_image_root)
                log.info(f'Assuming deployed image root is {deployed_image_root}')
        except KeyError:
            log.info('Config file is missing builder section.')
            deployed_image_root = '/'.join(['/var/tmp', os.getlogin(),
                                           'beeflow_deployed_containers'])
            # Make sure conf_file path exists
            os.makedirs(deployed_image_root, exist_ok=True)
            # Make sure path is absolute
            deployed_image_root = bc.resolve_path(deployed_image_root)
            log.info(f'Assuming deployed image root is {deployed_image_root}')
        finally:
            self.deployed_image_root = deployed_image_root
            os.makedirs(self.deployed_image_root, exist_ok=True)
            bc.modify_section('user', 'builder', {'deployed_image_root': self.deployed_image_root})
            log.info(f'Deployed image root directory is: {self.deployed_image_root}')
            log.info("Wrote deployed image root to user BeeConfig file.")
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
        bc.modify_section('user', 'builder', {'container_type': 'charliecloud'})
        self.task = task
        self.docker_image_id = None
        self.container_name = None
        dockerRequirements = set()
        try:
            requirement_DockerRequirements = self.task.requirements['DockerRequirement'].keys()
            dockerRequirements = dockerRequirements.union(requirement_DockerRequirements)
            log.info('task {} requirement DockerRequirements: {}'.
                     format(self.task.id, set(requirement_DockerRequirements)))
        except (TypeError, KeyError):
            log.info('task {} requirements has no DockerRequirements'.format(self.task.id))
        try:
            hint_DockerRequirements = self.task.hints['DockerRequirement'].keys()
            dockerRequirements = dockerRequirements.union(hint_DockerRequirements)
            log.info('task {} hint DockerRequirements: {}'.format(self.task.id,
                                                                  set(hint_DockerRequirements)))
        except (TypeError, KeyError):
            log.info('task {} hints has no DockerRequirements'.format(self.task.id))
        log.info('task {} union DockerRequirements consist of: {}'.format(self.task.id,
                                                                          dockerRequirements))
        exec_superset = self.resolve_priority()
        self.exec_list = [i for i in exec_superset if i[1] in dockerRequirements]
        log_exec_list = [i[1] for i in self.exec_list]
        log.info('task {} DockerRequirement execution order will be: {}'.format(self.task.id,
                                                                                log_exec_list))
        log.info('Execution order pre-empts hint/requirement status.')

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
        if req_addr:
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
                shutil.rmtree('/var/tmp/'+os.getlogin()+'/ch-image/'+ch_build_addr)
            except FileNotFoundError:
                pass

        # Out of excuses. Pull the image.
        cmd = (f'ch-image pull {addr}\n'
               f'ch-convert -i ch-image -o tar {ch_build_addr} {self.container_archive}/{ch_build_addr}.tar.gz'
               )
        return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              check=True, shell=True)

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

        log.warning('Charliecloud does not have the concept of a layered image tarball.')
        log.warning('Did you mean to use dockerImport?')
        if req_dockerload:
            log.warning('dockerLoad specified as requirement.')
            return 1
        return 0

    def dockerFile(self, task_dockerfile=None, force=False):
        """CWL compliant dockerFile.

        CWL spec 09-23-2020: Supply the contents of a Dockerfile
        which will be built using docker build. We have discussed implementing CWL
        change to expect a file handle instead of file contents, and use the file
        handle expectation here.
        """
        # containerName is always processed before dockerFile, so safe to assume it exists
        # otherwise, raise an error.
        if self.container_name is None:
            log.error("dockerFile may not be specified without containerName")
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
        if req_dockerfile:
            task_dockerfile = req_dockerfile
        elif hint_dockerfile:
            task_dockerfile = hint_dockerfile

        if not task_dockerfile:
            log.error("dockerFile not specified as task attribute or parameter.")
            return 1

        # Create context directory to use as Dockerfile context, use container name so user
        # can prep the directory with COPY sources as needed.
        context_dir = os.path.expanduser('~')
        log.info('Context directory will be {}.'.format(context_dir))

        # Determine name for successful build target
        ch_build_addr = self.container_name.replace('/', '%')

        ch_build_target = '/'.join([self.container_archive, ch_build_addr]) + '.tar.gz'
        log.info('Build will create tar ball at {}'.format(ch_build_target))
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

        # Out of excuses. Build the image.
        log.info('Context directory configured. Beginning build.')
        cmd = (f'ch-image build -t {self.container_name} -f {task_dockerfile} {context_dir}\n'
               f'ch-convert -i ch-image -o tar {ch_build_addr} {self.container_archive}/{ch_build_addr}.tar.gz'
               )
        log.info('Executing: {}'.format(cmd))
        return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              check=True, shell=True)

    def dockerImport(self, param_import=None):
        """CWL compliant dockerImport.

        CWL spec 09-23-2020: Provide HTTP URL to download and
        gunzip a Docker images using docker import. The param_import
        may be used to override DockerReuirement specs.
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
            if req_import:
                task_import = req_import
            elif hint_import:
                task_import = hint_import
            # Set import
            import_input_path = task_import

        # Pull the image.
        file_name = crt_driver.get_ccname(import_input_path)
        cmd = (f'ch-convert {import_input_path} {self.deployed_image_root}/{file_name}')
        log.info(f'Docker import: Assuming container name is {import_input_path}. Is this correct?')
        return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              check=True, shell=True)

    def dockerImageId(self, param_imageid=None):
        """CWL compliant dockerImageId.

        A divergence from the CWL spec. Docker image Id is defined by docker as a checksum
        on a container, not a human-readable name. The Docker image ID must be produced after
        the container is build, and can not be used to tag the container for that reason.
        The param_imageid may be used to override DockerRequirement specs.
        """
        # Parameter takes precedence
        if param_imageid:
            self.docker_image_id = param_imageid
        # If previously set by param, return 0 and ignore task.
        if self.docker_image_id:
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
        task_imageid = None
        if req_imageid:
            task_imageid = req_imageid
        elif hint_imageid:
            task_imageid = hint_imageid

        # Set imageid
        self.docker_image_id = task_imageid

        # If task and parameter still doesn't specify image_id, consider this an error.
        if self.docker_image_id:
            return 0
        return 1

    def dockerOutputDirectory(self, param_output_directory=None):
        """CWL compliant dockerOutputDirectory.

        CWL spec 09-23-2020: Set the designated output directory
        to a specific location inside the Docker container. The
        param_output_directory may be used to override DockerRequirement
        specs.
        """
        # Allow parameter over-ride.
        if param_output_directory:
            self.container_output_path = param_output_directory
        return 0

    def copyContainer(self, force=False):
        """CWL extension, copy an existing container into the build archive.

        If you have a container tarball, and all you need to do is stage it,
        that is, all you need to do is copy it to a location that BEE knows,
        use this to put the container into the build archive.
        """
        # Need container_path to know how dockerfile should be named, else fail
        try:
            # Try to get Hints
            hint_container_path = self.task.hints['DockerRequirement']['copyContainer']
        except (KeyError, TypeError):
            # Task Hints are not mandatory. No container_path specified in task hints.
            hint_container_path = None
        try:
            # Try to get Requirements
            req_container_path = self.task.requirements['DockerRequirement']['copyContainer']
        except (KeyError, TypeError):
            # Task Requirements are not mandatory. No container_path specified in task reqs.
            req_container_path = None

        # Prefer requirements over hints
        if req_container_path:
            task_container_path = req_container_path
        elif hint_container_path:
            task_container_path = hint_container_path

        if not task_container_path:
            log.error("copyContainer: You must specify the path to an existing container.")
            return 1

        if self.container_name:
            copy_target = '/'.join([self.container_archive, self.container_name + '.tar.gz'])
        else:
            copy_target = '/'.join([self.container_archive, os.path.basename(task_container_path)])
        log.info('Build will copy a container to {}'.format(copy_target))
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
        log.info('Executing: {}'.format(cmd))
        return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              check=True, shell=True)

    def containerName(self):
        """CWL extension, need a way to refer to containers human-readable name.

        The CWL spec currently uses dockerImageId to refer to the name of a container
        but this is explicitly not how Docker defines it. We need a way to name
        containers in a human readable format.
        """
        try:
            # Try to get Hints
            hint_container_name = self.task.hints['DockerRequirement']['containerName']
        except (KeyError, TypeError):
            # Task Hints are not mandatory. No container_name specified in task hints.
            hint_container_name = None
        try:
            # Try to get Requirements
            req_container_name = self.task.requirements['DockerRequirement']['containerName']
        except (KeyError, TypeError):
            # Task Requirements are not mandatory. No container_name specified in task reqs.
            req_container_name = None

        # Prefer requirements over hints
        if req_container_name:
            task_container_name = req_container_name
        elif hint_container_name:
            task_container_name = hint_container_name

        if not task_container_name and self.docker_image_id is None:
            log.error("containerName: You must specify the containerName or dockerImageId")
            return 1
        self.container_name = task_container_name
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

    def dockerPull(self, addr=None, force=False):
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

    def dockerFile(self, task_dockerfile=None, force=False):
        """CWL compliant dockerFile.

        CWL spec 09-23-2020: Supply the contents of a Dockerfile
        which will be built using docker build.
        """

    def dockerImport(self, param_import=None):
        """CWL compliant dockerImport.

        CWL spec 09-23-2020: Provide HTTP URL to download and
        gunzip a Docker images using docker import. The param_import
        may be used to override DockerRequirement specs.
        """

    def dockerImageId(self, param_imageid=None):
        """CWL compliant dockerImageId.

        CWL spec 09-23-2020: The image id that will be used for
        docker run. May be a human-readable image name or the
        image identifier hash. May be skipped if dockerPull is
        specified, in which case the dockerPull image id must be
        used. The param_imageid may be used to override DockerRequirement
        specs.
        """

    def dockerOutputDirectory(self, param_output_directory=None):
        """CWL compliant dockerOutputDirectory.

        CWL spec 09-23-2020: Set the designated output directory
        to a specific location inside the Docker container. The
        param_output_directory may be used to override DockerRequirement
        specs.
        """
# Ignore snake_case requirement to enable CWL compliant names. (C0103)
# Ignore "too many statements". Some of these methods are long, and that's ok (R0915)
# Ignore W0231: linter doesn't know about abstract classes, it's ok to now call the parent __init__
# Ignore W1202: Using fstrings does not cause us any issues in logging currently, improves
#               readibility as is
# pylama:ignore=C0103,R0915,W0231,W1202

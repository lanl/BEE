
"""BEE Cloud Installer Script."""

import argparse
import base64
import configparser
import os
import subprocess
import sys
import tempfile
import time

import beeflow.cloud as cloud
from beeflow.common.config_driver import BeeConfig


class CloudLauncherError(Exception):
    """Cloud launcher error class."""

    def __init__(self, msg):
        """Cloud launcher error constructor."""
        self.msg = msg


def launch_tm(provider, private_key_file, bee_user, launch_cmd, head_node,
              tm_listen_port, wfm_listen_port):
    """Start the Task Manager on the remote head node."""
    print('Launching the Remote Task Manager')
    ip_addr = provider.get_ext_ip_addr(head_node)

    # Now start the Task Manager
    tm_proc = subprocess.Popen([
        'ssh',
        '-i', private_key_file,
        '-o', 'StrictHostKeyChecking=no',
        '-o', 'ConnectTimeout=8',
        f'{bee_user}@{ip_addr}',
        # f'{env_cmd}; python -m beeflow.task_manager ~/.config/beeflow/bee.conf',
        launch_cmd,
    ])
    time.sleep(10)
    if tm_proc.poll() is not None:
        raise RuntimeError('Failed to launch the Remote Task Manager')

    # Set up the connection
    try:
        tun_proc = subprocess.run([
            'ssh',
            f'{bee_user}@{ip_addr}',
            '-i', private_key_file,
            # The TM is listening on the remote machine
            '-L', f'{tm_listen_port}:localhost:{tm_listen_port}',
            # The WFM is listening on this machine
            '-R', f'{wfm_listen_port}:localhost:{wfm_listen_port}',
            '-N',
            '-o', 'ExitOnForwardFailure=yes',
            '-o', 'StrictHostKeyChecking=no',
            # Required in order to allow port forwarding
            '-o', 'UserKnownHostsFile=/dev/null',
        ])
    finally:
        print('Killing the task manager')
        tm_proc.kill()


if __name__ == '__main__':
    # Argument parsing
    parser = argparse.ArgumentParser(description='BEE Cloud Installer')
    parser.add_argument('config_file', help='bee.conf file')
    parser.add_argument('--setup-cloud', action='store_true', help='set up the remote cloud')
    parser.add_argument('--tm', action='store_true', help='start the TM')
    parser.add_argument('--name', type=str, help='unique name of stack or set of cloud instances', required=True)
    args = parser.parse_args()

    # Get configuration information
    bc = BeeConfig(userconfig=args.config_file, workload_scheduler='Simple')
    if not bc.userconfig.has_section('cloud'):
        sys.exit('Missing [cloud] section in the bee.conf file')
    bee_workdir = bc.userconfig.get('DEFAULT', 'bee_workdir')

    # Get the component ports for forwarding connections
    wfm_listen_port = bc.userconfig['workflow_manager'].get('listen_port')
    tm_listen_port = bc.userconfig['cloud'].get('tm_listen_port')

    private_key_file = bc.userconfig['cloud'].get('private_key_file',
                                                  os.path.join(bee_workdir, 'bee_key'))
    bee_user = bc.userconfig['cloud'].get('bee_user', cloud.BEE_USER)
    # bee_dir = bc.userconfig['cloud'].get('bee_dir', None)
    launch_cmd = bc.userconfig['cloud'].get('tm_launch_cmd', None)
    name = bc.userconfig['cloud'].get('name', None)
    head_node = bc.userconfig['cloud'].get('head_node', 'bee-head-node')
    template_file = bc.userconfig['cloud'].get('template_file')

    # Get the cloud provider configuration
    provider = bc.userconfig['cloud'].get('provider', None)
    if provider is None:
        raise cloud.CloudError('No `provider` option was specified. This is required for Cloud setup.')
    provider_config = f'cloud.{provider.lower()}'
    if not bc.userconfig.has_section(provider_config):
        raise cloud.CloudError('Missing provider configuration file')
    # Now get the provider interface
    kwargs = dict(bc.userconfig[provider_config])
    provider = cloud.get_provider(provider, **kwargs)

    if args.setup_cloud:
        print('Creating cloud from template...')
        provider.create_from_template(template_file)
        print('Setup complete')
    if args.tm:
        launch_tm(provider=provider, private_key_file=private_key_file,
                  bee_user=bee_user, launch_cmd=launch_cmd, head_node=head_node,
                  wfm_listen_port=wfm_listen_port,
                  tm_listen_port=tm_listen_port)


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


def setup(provider, template_file):
    """Setup the cloud cluster.

    Returns the IP address of the cluster head node and the directory of the
    BEE source code on the head node.
    :rtype tuple (str, str)
    """
    print('Creating from template...')
    provider.create_from_template(template_file)
    print('Waiting for setup completion...')
    provider.wait()


def srcdir(src):
    """Get the source directory for the untarred source."""
    basename = os.path.basename(src)
    return basename.split('.')[0]


def tm(provider, private_key_file, head_node, bee_user, bee_srcdir, tm_listen_port, wfm_listen_port, env_cmd):
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
        f'{env_cmd}; python -m beeflow.task_manager ~/.config/beeflow/bee.conf',
        # f'cd ~/{bee_srcdir}; . ./venv/bin/activate; python -m beeflow.task_manager ~/.config/beeflow/bee.conf',
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
    parser = argparse.ArgumentParser(description='BEE Cloud Installer')
    parser.add_argument('config_file', help='bee.conf file')
    parser.add_argument('--setup-cloud', action='store_true', help='set up the remote cloud')
    parser.add_argument('--tm', action='store_true', help='start the TM')
    args = parser.parse_args()

    # Get all configuration information
    bc = BeeConfig(userconfig=args.config_file, workload_scheduler='Simple')
    if not bc.userconfig.has_section('cloud'):
        print('Missing [cloud] section in the bee.conf file', file=sys.stderr)
        sys.exit(1)
    bee_workdir = bc.userconfig.get('DEFAULT', 'bee_workdir')
    head_node = bc.userconfig['cloud'].get('head_node', 'bee-head-node')
    private_key_file = bc.userconfig['cloud'].get('private_key_file',
                                                  os.path.join(bee_workdir, 'bee_key'))
    bee_user = bc.userconfig['cloud'].get('bee_user', cloud.BEE_USER)
    bee_srcdir = bc.userconfig['cloud'].get('bee_srcdir', None)
    env_cmd = bc.userconfig['cloud'].get('env_cmd', None)
    # Get the component ports for forwarding connections
    wfm_listen_port = bc.userconfig['workflow_manager'].get('listen_port')
    tm_listen_port = bc.userconfig['task_manager'].get('listen_port')
    # Get the cloud provider configuration
    provider = bc.userconfig['cloud'].get('provider', None)
    if provider is None:
        raise cloud.CloudError('No `provider` option was specified. This is required for Cloud setup.')
    provider_config = f'cloud.{provider}'
    if not bc.userconfig.has_section(provider_config):
        raise cloud.CloudError('Missing provider configuration file')
    # Now get the provider interface
    kwargs = dict(bc.userconfig[provider_config])
    provider = cloud.get_provider(provider, **kwargs)

    if args.setup_cloud:
        setup(provider=provider, head_node=head_node, bee_user=bee_user,
              private_key_file=private_key_file)
    if args.tm:
        tm(provider=provider, private_key_file=private_key_file, head_node=head_node,
           bee_user=bee_user, bee_srcdir=bee_srcdir,
           wfm_listen_port=wfm_listen_port, tm_listen_port=tm_listen_port, env_cmd=env_cmd)

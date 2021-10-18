
"""BEE Cloud Installer Script."""

import argparse
import os
import subprocess
import sys
import time

import beeflow.common.cloud as cloud
from beeflow.common.config_driver import BeeConfig


def run(private_key_file, bee_user, ip_addr, cmd):
    """Run a command on the remote host."""
    cp = subprocess.run([
        'ssh',
        '-i', private_key_file,
        '-o', 'StrictHostKeyChecking=no',
        '-o', 'ConnectTimeout=8',
        f'{bee_user}@{ip_addr}',
        cmd,
    ])
    return cp.returncode


def scp(bee_user, ip_addr, priv_key_file, src, dst):
    """SCP a file in src to dst on the remote machine."""
    cp = subprocess.run([
        'scp',
        '-i', priv_key_file,
        '-o', 'StrictHostKeyChecking=no',
        src,
        f'{bee_user}@{ip_addr}:{dst}',
    ])
    if cp.returncode != 0:
        raise RuntimeError(f'Could not copy file "{src}" to "{dst}" on the remote machine')


def copy_files_to_instance(provider, bee_user, private_key_file, head_node,
                           copy_files):
    """Copy files over to the instance."""
    print('Starting file copy step')
    ip_addr = provider.get_ext_ip_addr(head_node)
    # `copy_files` is in the format src0:dst0,src1:dst1,...,srcn:dstn
    copy_files = [tuple(pair.split(':')) for pair in copy_files.split(',')]
    for src, dst in copy_files:
        scp(bee_user, ip_addr, private_key_file, src, dst)
    print('Finished')


def launch_tm(provider, private_key_file, bee_user, launch_cmd, head_node,
              tm_listen_port, wfm_listen_port):
    """Start the Task Manager on the remote head node."""
    print('Launching the Remote Task Manager')
    ip_addr = provider.get_ext_ip_addr(head_node)
    tm_proc = None

    try:
        # Now start the Task Manager
        tm_proc = subprocess.Popen([
            'ssh',
            '-i', private_key_file,
            '-o', 'StrictHostKeyChecking=no',
            '-o', 'ConnectTimeout=8',
            f'{bee_user}@{ip_addr}',
            launch_cmd,
        ])
        time.sleep(10)
        if tm_proc.poll() is not None:
            raise RuntimeError('Failed to launch the Remote Task Manager')

        # Set up the connection
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
    except KeyboardInterrupt:
        print('Got keyboard interrupt, quitting')
    finally:
        if tm_proc is not None:
            print('Killing the task manager')
            # TODO: This could be done better using a pidfile
            run(private_key_file, bee_user, ip_addr, 'pkill python')


if __name__ == '__main__':
    # Argument parsing
    parser = argparse.ArgumentParser(description='BEE Cloud Installer')
    parser.add_argument('config_file', help='bee.conf file')
    parser.add_argument('--setup-cloud', action='store_true', help='set up the remote cloud')
    parser.add_argument('--copy', action='store_true', help='copy over files in the config')
    parser.add_argument('--tm', action='store_true', help='start the TM')
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
    head_node = bc.userconfig['cloud'].get('head_node', 'bee-head-node')
    template_file = bc.userconfig['cloud'].get('template_file')
    copy_files = bc.userconfig['cloud'].get('copy_files', None)

    # Get the cloud provider configuration
    provider = bc.userconfig['cloud'].get('provider', None)
    if provider is None:
        raise cloud.CloudError('No `provider` option was specified. This is required for Cloud setup.')
    provider_config = f'cloud.{provider.lower()}'
    if not bc.userconfig.has_section(provider_config):
        raise cloud.CloudError('Missing provider configuration file')
    # Get the keyword arguments for the provider class
    kwargs = dict(bc.userconfig[provider_config])
    # Remove defaults (we have to be careful here not to use keys that will be
    # in the DEFAULT section -- this should probably be documented)
    kwargs = {key: kwargs[key] for key in kwargs if key not in bc.userconfig.defaults()}
    # Now get the provider interface
    provider = cloud.get_provider(provider, **kwargs)

    if args.setup_cloud:
        print('Creating cloud from template...')
        provider.create_from_template(template_file)
        time.sleep(20)
        print('Setup complete')
    if args.copy and copy_files is not None:
        copy_files_to_instance(provider=provider, bee_user=bee_user,
                               private_key_file=private_key_file,
                               head_node=head_node, copy_files=copy_files)
    if args.tm:
        launch_tm(provider=provider, private_key_file=private_key_file,
                  bee_user=bee_user, launch_cmd=launch_cmd, head_node=head_node,
                  wfm_listen_port=wfm_listen_port,
                  tm_listen_port=tm_listen_port)

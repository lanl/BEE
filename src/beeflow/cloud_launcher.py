"""BEE Cloud Installer Script."""
import argparse
import os
import subprocess
import sys
import time
import yaml

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
    for file in copy_files:
        src = file['src']
        dst = file['dst']
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
    parser.add_argument('provider_config', help='provider config yaml file')
    parser.add_argument('--config_file', help='bee.conf file')
    parser.add_argument('--setup-cloud', action='store_true', help='set up the remote cloud')
    parser.add_argument('--copy', action='store_true', help='copy over files in the config')
    parser.add_argument('--tm', action='store_true', help='start the TM')
    parser.add_argument('--fake', action='store_true',
                        help='when given along with the --setup-cloud, run all templating code, but do not actually make any API calls')
    args = parser.parse_args()

    # Get configuration information
    if args.config_file is not None:
        bc = BeeConfig(userconfig=args.config_file, workload_scheduler='Simple')
    else:
        bc = BeeConfig(workload_scheduler='Simple')
    # Load the provider config file
    cfg = yaml.load(open(args.provider_config), Loader=yaml.Loader)
    bee_workdir = bc.userconfig.get('DEFAULT', 'bee_workdir')

    # Get the component ports for forwarding connections
    wfm_listen_port = cfg['wfm_listen_port']
    tm_listen_port = cfg['tm_listen_port']
    private_key_file = cfg['private_key_file']
    bee_user = cfg['bee_user']
    launch_cmd = cfg['tm_launch_cmd']
    head_node = cfg['head_node']
    template_file = cfg['template_file']
    copy_files = cfg['copy_files']

    provider = cfg['provider']
    kwargs = cfg['provider_parameters']
    # Add in the default parameters
    kwargs.update({'beeflow_{}'.format(name): cfg[name] for name in cfg if name != 'provider_parameters'})
    # Get the cloud provider configuration
    provider = cloud.get_provider(provider, fake=args.fake, **kwargs)

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

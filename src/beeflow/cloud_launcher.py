"""BEE Cloud Launcher Script."""

import argparse
import base64
import json
import os
import subprocess
import sys
import time

import beeflow.cloud as cloud
from beeflow.common.config_driver import BeeConfig


# TODO: Refactor this code

def generate_private_key(keyfile):
    """Generate the SSH private key."""
    cp = subprocess.run(['ssh-keygen', '-N', '', '-f', keyfile])
    if cp.returncode != 0:
        raise RuntimeError('ssh-keygen failed')


def load_config():
    """Load the configuration, setting any defaults."""
    parser = argparse.ArgumentParser(description='BEE Cloud Launcher')
    parser.add_argument('config_file', default=None, help='bee.conf file')
    parser.add_argument('--setup', action='store_true',
                        help='set up the remote cloud based on bee.conf')
    parser.add_argument('--install-tm', action='store_true',
                        help='install the Task Manager')
    parser.add_argument('--tm', action='store_true',
                        help='start the Task Manager on the cloud and connect to it')
    parser.add_argument('--resource-id', help='resource ID for the Task Manager')
    args = parser.parse_args()

    if args.config_file is not None:
        bc = BeeConfig(userconfig=args.config_file)
    else:
        bc = BeeConfig()

    # TODO: Check for missing sections
    assert bc.userconfig.has_section('cloud')
    bee_workdir = bc.userconfig.get('DEFAULT', 'bee_workdir')
    return {
        # Config file options
        'bee_workdir': bee_workdir,
        # Cloud specific options
        'cloud_workdir': bc.userconfig.get('cloud', 'cloud_workdir'),
        'provider': bc.userconfig['cloud'].get('provider', 'Google'),
        'node_count': int(bc.userconfig['cloud'].get('node_count', '2')),
        'ram_per_vcpu': int(bc.userconfig['cloud'].get('ram_per_vcpu', '2')),
        'vcpu_per_node': int(bc.userconfig['cloud'].get('vcpu_per_node', '1')),
        'bee_user': bc.userconfig['cloud'].get('bee_user', 'bee'),
        'private_key_file': bc.userconfig['cloud'].get('private_key_file',
                                               os.path.join(bee_workdir, 'bee_key')),
        # TODO: Need to set up the cloud storage
        'storage': bc.userconfig['cloud'].get('storage', None),
        # Tarball containing the BEE code
        'bee_code': bc.userconfig['cloud'].get('bee_code'),
        # Ports
        'tm_listen_port': bc.userconfig['task_manager'].get('listen_port',
                                                            bc.default_tm_port),
        'wfm_listen_port': bc.userconfig['workflow_manager'].get('listen_port',
                                                                 bc.default_wfm_port),
        # Command-line argument options
        'setup': args.setup,
        'install_tm': args.install_tm,
        'tm': args.tm,
        'resource_id': args.resource_id if args.resource_id is not None else '',
        'config_file': os.path.expanduser(args.config_file),
    }


def run(bee_user, ip_addr, priv_key_file, cmd):
    """Run a command on remote machine."""
    cp = subprocess.run([
        'ssh',
        '-i', priv_key_file,
        '-o', 'StrictHostKeyChecking=no',
        f'{bee_user}@{ip_addr}',
        cmd,
    ])
    if cp.returncode != 0:
        raise RuntimeError(f'Could not run "{cmd}" on the remote machine')


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


def install_tm(priv_key_file, ip_addr, bee_code, config_file,
               bee_user=cloud.BEE_USER, **kwargs):
    """Install the Task Manager on the remote machine.

    Returns the directory containing the BEE source code.
    :rtype string
    """
    # Copy over the bee code
    scp(bee_user, ip_addr, priv_key_file, conf['bee_code'], '~/')

    # basename = os.path.basename(conf['bee_code'])
    basename = os.path.basename(bee_code)
    bee_srcdir = basename.split('.')[0]
    # Script to install BEE
    bee_install = [
        '#!/bin/sh\n',
        f'tar -xvf {basename}\n',
        f'cd {bee_srcdir}\n',
        'python3 -m venv venv\n',
        '. ./venv/bin/activate\n',
        'pip install --upgrade pip\n',
        'pip install poetry\n',
        'poetry install\n',
        # Also create the config directory
        'mkdir -p ~/.config/beeflow\n',
    ]
    bee_install = ''.join(bee_install)
    # Send the script as base64 over to the machine
    bee_install = bytes(bee_install, encoding='utf-8')
    bee_install_b64 = str(base64.b64encode(bee_install), encoding='utf-8')

    run(bee_user, ip_addr, priv_key_file, f'echo {bee_install_b64} | base64 -d > install.sh')

    # Run the install script
    run(bee_user, ip_addr, priv_key_file, 'sh install.sh')

    # Make a copy of the bee.conf and make edits to it for running the Task
    # Manager with cloud.BEE_USER
    tmp_bee_conf = f'/tmp/bee_{os.getuid()}.conf'
    # with open(os.path.expanduser('~/.config/beeflow/bee.conf')) as fp:
    with open(config_file) as fp:
        data = fp.read()
        data = data.replace(conf['bee_workdir'], f'/home/{bee_user}/.beeflow')
        with open(tmp_bee_conf, 'w') as fp:
            fp.write(data)

    # Copy over the modified bee.conf
    scp(bee_user, ip_addr, priv_key_file, tmp_bee_conf, '~/.config/beeflow/bee.conf')

    return bee_srcdir


def run_tm(bee_user, ip_addr, priv_key_file, bee_srcdir, resource_id=''):
    """Run the Task Manager."""
    # Now start the Task Manager
    tm_proc = subprocess.Popen([
        'ssh',
        '-i', priv_key_file,
        '-o', 'StrictHostKeyChecking=no',
        '-o', 'ConnectTimeout=8',
        f'{bee_user}@{ip_addr}',
        # f'cd {dirname}; . ./venv/bin/activate; beeflow --tm --debug',
        f'cd {bee_srcdir}; . ./venv/bin/activate; python -m beeflow.task_manager ~/.config/beeflow/bee.conf {resource_id}',
    ])
    time.sleep(10)
    if tm_proc.poll() is not None:
        raise RuntimeError('Failed to launch the Remote Task Manager')
    return tm_proc


def setup(conf, priv_key_file):
    """Setup the cloud cluster.

    Returns the IP address of the cluster head node and the directory of the
    BEE source code on the head node.
    :rtype tuple (str, str)
    """
    provider = cloud.get_provider(conf['provider'])
    bee_user = conf['bee_user']

    # Generate the private key if it doesn't exist yet
    if not os.path.exists(priv_key_file):
        generate_private_key(priv_key_file)

    # Set up the Cloud
    c = cloud.Cloud(provider, priv_key_file=priv_key_file, bee_user=bee_user)

    # Create the head node
    print('Creating head node')
    head_node = c.create_node(ram_per_vcpu=conf['ram_per_vcpu'],
                              vcpu_per_node=conf['vcpu_per_node'], ext_ip=True)
    # Create the worker nodes
    nodes = []
    for i in range(conf['node_count']):
        print('Creating node', i)
        nodes.append(c.create_node(ram_per_vcpu=2, vcpu_per_node=2,
                                   ext_ip=False))

    # Now set up the interconnect between the nodes
    c.setup_interconnect()

    # Wait for set up to complete
    print('Waiting for cloud setup...')
    c.wait()
    # ip_addr = head_node.get_ext_ip()
    return head_node.get_ext_ip()

    # Copy over the BEE code and install it
    # bee_srcdir = install_tm(conf, priv_key_file, ip_addr)
    # return ip_addr, bee_srcdir


def connect(ip_addr, priv_key_file, tm_listen_port, wfm_listen_port, bee_user, **kwargs):
    """Connect to the remote head node and wait."""
    # Open SSH Tunnel or VPN to the remote Task Manager
    print('Setting up SSH tunnel to head node')
    tun_proc = subprocess.run([
        'ssh',
        f'{bee_user}@{ip_addr}',
        '-i', priv_key_file,
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


class CloudLauncher:
    """Cloud launcher."""

    def __init__(self, conf):
        """Cloud launcher constructor."""
        self._conf = conf
        self._info = cloud.CloudInfo(
            os.path.join(conf['cloud_workdir'], 'cloud-info.json')
        )
        # TODO: Remove this temporary hack
        # self._priv_key_file = os.path.expanduser('~/bee/chameleon-bee-key.pem')
        # self._priv_key_file = os.path.expanduser('~/bee/bee_key')
        self._priv_key_file = conf['private_key_file']

    def setup(self):
        """Set up the cloud."""
        # Set up the cloud
        ip_addr = setup(self._conf, self._priv_key_file)
        self._info.set('head_node_ip_addr', ip_addr)
        self._info.save()
        # Write out new cloud information
        print(f'Cloud setup should be complete. You should check by logging into the remote head node ({self._conf["bee_user"]}@{ip_addr}).')

    def install_tm(self):
        """Install the Task Manager."""
        # Install the Task Manager
        # Copy over the BEE code and install it
        bee_srcdir = install_tm(self._priv_key_file, self._info.get('head_node_ip_addr'),
                                **self._conf)
        # Write out cloud information
        # info.set('head_node_ip_addr', ip_addr)
        self._info.set('bee_srcdir', bee_srcdir)
        self._info.save()
        print('Task Manager is now installed on the remote head node.')

    def tm(self):
        """Start the Task Manager on the remote head node."""
        print('Launching the Remote Task Manager')
        tm_proc = run_tm(self._conf['bee_user'], self._info.get('head_node_ip_addr'), self._priv_key_file, self._info.get('bee_srcdir'), self._conf['resource_id'])
        # Set up the connection
        try:
            connect(self._info.get('head_node_ip_addr'), self._priv_key_file, **self._conf)
        finally:
            print('Killing the task manager')
            tm_proc.kill()


# TODO: Use a more object oriented/encapsulated design here

# TODO: Add a general connect option to only connect to the remote head node without setup
if __name__ == '__main__':
    conf = load_config()
    launcher = CloudLauncher(conf)
    if conf['setup']:
        launcher.setup()
    if conf['install_tm']:
        launcher.install_tm()
    if conf['tm']:
        launcher.tm()

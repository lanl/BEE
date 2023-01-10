"""BEE Cloud Installer Script."""
import argparse
import subprocess
import sys
import time
import yaml
import jinja2
import requests

from beeflow.common import cloud
from beeflow.common.config_driver import BeeConfig as bc


def run(private_key_file, bee_user, ip_addr, cmd):
    """Run a command on the remote host."""
    proc = subprocess.run([
        'ssh',
        '-i', private_key_file,
        '-o', 'StrictHostKeyChecking=no',
        '-o', 'ConnectTimeout=8',
        f'{bee_user}@{ip_addr}',
        cmd,
    ], check=True)
    return proc.returncode


def scp(bee_user, ip_addr, priv_key_file, src, dst):
    """SCP a file in src to dst on the remote machine."""
    proc = subprocess.run([
        'scp',
        '-i', priv_key_file,
        '-o', 'StrictHostKeyChecking=no',
        src,
        f'{bee_user}@{ip_addr}:{dst}',
    ], check=True)
    if proc.returncode != 0:
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

        # Set up the connection with an SSH tunnel
        subprocess.run([
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
        ], check=True)
    except KeyboardInterrupt:
        print('Got keyboard interrupt, quitting')
    finally:
        if tm_proc is not None:
            print('Killing the task manager')
            # TODO: This could be done much better using a pidfile
            run(private_key_file, bee_user, ip_addr, 'pkill python')


def connect(provider, private_key_file, bee_user, head_node,
            tm_listen_port, wfm_listen_port, max_retries):
    """Connect to an already running TM."""
    ip_addr = provider.get_ext_ip_addr(head_node)
    tun_proc = subprocess.Popen([
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
    time.sleep(3)
    returncode = tun_proc.poll()
    # Ensure the SSH process is still running
    if returncode is not None:
        sys.exit(f'Tunnel set up failed with error: {returncode}')
    # Now continue until we can ping the Task Manager
    url = f'http://localhost:{tm_listen_port}/status'
    interval = 5
    # Keep trying to get a status from the Task Manager (this could probably be
    # done better with some sort of backoff algorithm)
    for _ in range(max_retries):
        print('Trying to connect to the TM')
        time.sleep(interval)
        try:
            resp = requests.get(url, timeout=60)
            status = resp.json()
            print(f'Connected to the TM with status "{status}"')
            return
        except requests.ConnectionError:
            pass
    # If we get here, then set up might be taking longer than interval *
    # max_retries or the set up failed somehow
    tun_proc.kill()
    sys.exit('Connection attempt to the TM failed')


def main():
    """Cloud launcher entry point."""
    # Argument parsing
    parser = argparse.ArgumentParser(description='BEE Cloud Installer')
    parser.add_argument('provider_config', help='provider config yaml file')
    parser.add_argument('--config_file', help='bee.conf file')
    parser.add_argument('--setup-cloud', action='store_true', help='set up the remote cloud')
    parser.add_argument('--copy', action='store_true', help='copy over files in the config')
    parser.add_argument('--tm', action='store_true', help='start the TM')
    parser.add_argument('--connect', action='store_true', help='connect to an already running TM')
    parser.add_argument('--debug', action='store_true',
                        help='debug the cloud template, don\'t make any API calls')
    parser.add_argument('--max-retries', default=124, type=int,
                        help='max number of retry attempts when used with the `--connect` option')
    args = parser.parse_args()

    # Get configuration information
    if args.config_file is not None:
        bc.init(userconfig=args.config_file, workload_scheduler='Simple')
    else:
        bc.init(workload_scheduler='Simple')
    # Load the provider config file
    with open(args.provider_config, 'r', encoding='utf-8') as fp:
        cfg = yaml.load(fp, Loader=yaml.Loader)

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
    provider = cloud.get_provider(provider, **cfg)

    if args.setup_cloud:
        print('Creating cloud from template...')
        with open(template_file, encoding='utf-8') as fp:
            tmpl = jinja2.Template(fp.read())
        tmpl_data = tmpl.render(**cfg)
        if args.debug:
            # Display the template
            sys.stdout.write(tmpl_data)
            sys.exit()
        provider.setup_cloud(tmpl_data)
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
    if args.connect:
        connect(provider=provider, private_key_file=private_key_file,
                bee_user=bee_user, head_node=head_node,
                wfm_listen_port=wfm_listen_port, tm_listen_port=tm_listen_port,
                max_retries=args.max_retries)


if __name__ == '__main__':
    main()
# Ignore R1732: Significant code restructuring required to fix
# Ignore W0511: This allows us to have TODOs in the code
# pylama:ignore=W0511,R1732

"""Module contains the code for launching redis subprocess."""
import os
import shutil
import subprocess

from beeflow.common import paths
from beeflow.common.deps import container_manager
from beeflow.common.config_driver import BeeConfig as bc

def setup_config(container):
    """Setup the redis config."""
    data_dir = 'data'
    os.makedirs(os.path.join(paths.redis_root(), data_dir), exist_ok=True)
    conf_name = 'redis.conf'
    conf_path = os.path.join(paths.redis_root(), conf_name)
    if container:
        mount_point = '/mnt'
    else:
        mount_point = paths.redis_root()
    with open(conf_path, 'w', encoding='utf-8') as fp:
        # Don't listen on TCP
        print('port 0', file=fp)
        print('dir', os.path.join(mount_point, data_dir), file=fp)
        print('maxmemory 2mb', file=fp)
        print('unixsocket', os.path.join(mount_point, paths.redis_sock_fname()), file=fp)
        print('unixsocketperm 700', file=fp)
    return conf_path


def start(log):
    """Start redis."""
    use_containers = bc.get("DEFAULT", "use_redis_container")
    if use_containers:
        container_path = paths.redis_container()
        if not container_manager.check_container_dir('redis'):
            print('Unpacking Redis image...')
            container_manager.create_image('redis')
        setup_config(container=True)
        cmd = [
            'ch-run',
            f'--bind={paths.redis_root()}:/mnt',
            container_path,
            'redis-server',
            '/mnt/redis.conf',
        ]

        # Ran into a strange "Failed to configure LOCALE for invalid locale name."
        # from Redis, so setting LANG=C. This could have consequences for UTF-8
        # strings.
        env = dict(os.environ)
        env['LANG'] = 'C'
        env['LC_ALL'] = 'C'
        proc = subprocess.Popen(cmd, env=env, stdout=log, stderr=log)
    else:
        conf_path = setup_config(container=False) 
        redis_exists = shutil.which('redis-server')
        cmd = ['redis-server', conf_path]

        if not redis_exists:
            spack_path = bc.get("DEFAULT", "spack_path")
            spec = "redis"
            # Need to add redis version checking
            bash_cmd = f'''
                source "{spack_path}/share/spack/setup-env.sh"
                spack load {spec}
                exec {" ".join(cmd)} 
            '''
            proc = subprocess.Popen(["bash", "-lc", bash_cmd], stdout=log, stderr=log)
        else:
            proc = subprocess.Popen(cmd, stdout=log, stderr=log)
    return proc

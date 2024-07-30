"""Module contains the code for launching redis subprocess."""
import os
import subprocess

from beeflow.common import paths


def start(log):
    """Start redis."""
    data_dir = 'data'
    os.makedirs(os.path.join(paths.redis_root(), data_dir), exist_ok=True)
    conf_name = 'redis.conf'
    container_path = paths.redis_container()
    # Dump the config
    conf_path = os.path.join(paths.redis_root(), conf_name)
    if not os.path.exists(conf_path):
        with open(conf_path, 'w', encoding='utf-8') as fp:
            # Don't listen on TCP
            print('port 0', file=fp)
            print('dir', os.path.join('/mnt', data_dir), file=fp)
            print('maxmemory 2mb', file=fp)
            print('unixsocket', os.path.join('/mnt', paths.redis_sock_fname()), file=fp)
            print('unixsocketperm 700', file=fp)
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
    return subprocess.Popen(cmd, env=env, stdout=log, stderr=log)

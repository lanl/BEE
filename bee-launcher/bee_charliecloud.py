# system
import os
import subprocess
from termcolor import cprint
# project
from host import Host

class BeeCharliecloud(object):
    def __init__(self, task_id, hostname, host, rank, task_conf, bee_vm_conf,
                 key_path, base_img, img, network_mode, storage_mode):

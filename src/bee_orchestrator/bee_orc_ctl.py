#!/usr/bin/env python
# system
import os
import socket
import Pyro4
import Pyro4.naming
import time
from json import load, dumps
from pwd import getpwuid
from subprocess import Popen
from termcolor import cprint
from time import sleep
# project
from exec_targets.bee_charliecloud.bee_charliecloud_launcher import \
    BeeCharliecloudLauncher as beeCC


@Pyro4.expose
class BeeLauncherDaemon(object):
    def __init__(self):
        print("Starting Bee orchestration controller..")
        self.__py_dir = os.path.dirname(os.path.abspath(__file__))
        self.beetask = None

    def create_task(self, beefile, file_name):
        print("Bee orchestration controller: received task creating request")
        exec_target = beefile['class']
        beetask_name = beefile.get('id', file_name + time.strftime("_%Y%m%d_%H%M%S"))
        if str(exec_target).lower() == 'bee-charliecloud':
            cprint("[" + beetask_name + "] Launched BEE-Charliecloud Instance!")
            self.beetask = beeCC(beetask_name, beefile)

    def launch_task(self):
        self.beetask.start()
    
    def create_and_launch_task(self, beefile, file_name):
        cprint("[" + file_name + ".beefile] Task received in current working "
                                 "directory: " + os.getcwd(), 'cyan')
        self.create_task(beefile, file_name)
        self.launch_task()

    def terminate_task(self, beetask_name):
        pass

    def delete_task(self, beetask_name):
        pass

    def list_all_tasks(self):
        pass


def main(beefile=None, file_name=None):
    """
    Prepare environment for daemon and launch (loop)
        https://pypi.org/project/Pyro4/
    :param beefile: Task to be launched once daemon launched
                    Full path to task (beefile) e.g. /var/tmp/test
    :param file_name: Beefile name (no .beefile)
    """
    open_port = get_open_port()
    update_system_conf(open_port)
    hmac_key = getpwuid(os.getuid())[0]
    os.environ["PYRO_HMAC_KEY"] = hmac_key
    Popen(['python', '-m', 'Pyro4.naming', '-p', str(open_port)])
    sleep(5)
    #############################################################
    # TODO: document daemon!!!
    #############################################################
    bldaemon = BeeLauncherDaemon()
    daemon = Pyro4.Daemon()
    bldaemon_uri = daemon.register(bldaemon)
    ns = Pyro4.locateNS(port=open_port, hmac_key=hmac_key)
    ns.register("bee_launcher.daemon", bldaemon_uri)
    cprint("Bee orchestration controller started.", 'cyan')

    # Launch task before starting daemon
    if beefile is not None:
        bldaemon.create_and_launch_task(beefile, file_name)

    daemon.requestLoop()


def update_system_conf(open_port):
    conf_file = str(os.path.expanduser('~')) + "/.bee/port_conf.json"
    with open(conf_file, 'r+') as fc:
        data = load(fc)
        data["pyro4-ns-port"] = open_port
        fc.seek(0)
        fc.write(dumps(data))
        fc.truncate()


def get_open_port():
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(("", 0))
        s.listen(1)
        port = s.getsockname()[1]
        s.close()
        return port


if __name__ == "__main__":
    main()

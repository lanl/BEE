# system
import Pyro4
import os
import getpass
import json
# project
from .beefile_manager import BeeflowLoader, BeefileLoader


class BeeFlow(object):
    def __init__(self, log, log_dest):
        # Logging configuration
        self.__log = log  # log flag (T/F)
        self.__log_dest = log_dest + ".flow"  # log file destination

        self.__pydir = os.path.dirname(os.path.abspath(__file__))
        self.__cwdir = os.getcwd()
        self.__hdir = os.path.expanduser('~')
        f = open(self.__hdir + "/.bee/bee_conf.json", "r")
        data = json.load(f)
        port = int(data["pyro4-ns-port"])
        ns = Pyro4.locateNS(port=port, hmac_key=getpass.getuser())
        uri = ns.lookup("bee_launcher.daemon")
        self.bldaemon = Pyro4.Proxy(uri)

    def launch(self, beeflow, beefiles):
        for beetask in beefiles:
            self.encode_cwd(beefiles[beetask])
        self.bldaemon.launch_beeflow(beeflow, beefiles)

    def encode_cwd(self, beefile):
        for run_conf in beefile['task_conf']['general_run']:
            run_conf['script'] = self.__cwdir + "/" + run_conf['script']
        for run_conf in beefile['task_conf']['mpi_run']:
            run_conf['script'] = self.__cwdir + "/" + run_conf['script']

    def main(self, beeflow):
        # Load beeflow file
        bf = BeeflowLoader(beeflow)
        beeflow = bf.get_beeflow()

        # Load each beefile
        beefiles = {}
        for task in beeflow:
            beefile = BeefileLoader(task).get_beefile()
            beefiles[task] = beefile

        self.launch(beeflow, beefiles)

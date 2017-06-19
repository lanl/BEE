#!/usr/bin/python                                                                                                       
import Pyro4
from beeflow_loader import BeeflowLoader
from beefile_loader import BeefileLoader
import sys
import getopt
import os
import json

class BeeComposer(object):
    def __init__(self):
        self.__pydir = os.path.dirname(os.path.abspath(__file__))
        self.__cwdir = os.getcwd()
        f = open(self.__pydir + "/bee_conf.json", "r")
        data = json.load(f)
        port = int(data["pyro4-ns-port"])
        ns = Pyro4.locateNS(port = port, hmac_key = os.getlogin())
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
            run_conf['script'] = self.__cwdir + "/"+ run_conf['script']


def main(argv):
    bee_composer = BeeComposer()
    beeflow = ""

    try:
        opts, args = getopt.getopt(argv, "f:", ["beeflow="])
    except getopt.GetoptError:
        print("Please provide beeflow file: -f/--beeflow <file>.")
        exit()
    
    for opt, arg in opts:
        if opt in ("-f", "--beeflow"):
            beeflow = arg

    # Load beeflow file
    bf = BeeflowLoader(beeflow)
    beeflow = bf.get_beeflow()
    
    # Load each beefile
    beefiles = {}
    for task in beeflow:
        beefile = BeefileLoader(task).get_beefile()
        beefiles[task] = beefile
    
    bee_composer.launch(beeflow, beefiles)
    

    
if __name__ == "__main__":
    main(sys.argv[1:])

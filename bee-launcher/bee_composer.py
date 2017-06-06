#!/usr/bin/python                                                                                                       
import Pyro4
from beeflow_loader import BeeflowLoader
from beefile_loader import BeefileLoader
import sys
import getopt

class BeeComposer(object):
    def __init__(self):
        self.bldaemon = Pyro4.Proxy("PYRONAME:bee_launcher.daemon")
    
    def launch(self, beeflow, beefiles):
        self.bldaemon.launch_beeflow(beeflow, beefiles)
    


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

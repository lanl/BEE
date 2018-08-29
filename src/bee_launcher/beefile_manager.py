# system
from yaml import load, YAMLError
from termcolor import cprint


class BeefileLoader(object):
    def __init__(self, file_name):
        try:
            stream = open("{}.beefile".format(file_name), "r")
            self.beefile = load(stream)
        except YAMLError as err:
            cprint(err, "red")
            exit(1)


class BeeflowLoader(object):
    def __init__(self, flow_name):
        try:
            stream = open("{}.beeflow".format(flow_name), "r")
            self.beefile = load(stream)
        except YAMLError as err:
            cprint(err, "red")
            exit(1)

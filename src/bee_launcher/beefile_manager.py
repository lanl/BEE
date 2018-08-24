# system
from yaml import load


class BeefileLoader(object):
    def __init__(self, file_name):
        stream = open("{}.beefile".format(file_name), "r")
        self.beefile = load(stream)


class BeeflowLoader(object):
    def __init__(self, flow_name):
        stream = open("{}.beeflow".format(flow_name), "r")
        self.beefile = load(stream)


import json

class BeeflowLoader(object):
    def __init__(self, flow):
        f = open("./{}.beeflow".format(flow),"r")
        self.__beeflow = json.load(f)
        
    def get_beeflow(self):
        return self.__beeflow


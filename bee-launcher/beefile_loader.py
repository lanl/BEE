import json

class BeefileLoader(object):
    def __init__(self, task):
        f = open("./{}.beefile".format(task),"r")
        self.__beefile = json.load(f)

    def get_beefile(self):
        return self.__beefile

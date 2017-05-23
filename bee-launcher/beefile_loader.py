import json

class BeefileLoader(object):
    def __init__(self, beefile):
        self.__beefile = open("./{}".format(beefile),"r")
        self.__bee_conf = json.load(self.__beefile)
        
    def get_job_conf(self):
        return self.__bee_conf['job_conf']

    def get_docker_conf(self):
        return self.__bee_conf['docker_conf']

    def get_bee_vm_conf(self):
        return self.__bee_conf['exec_env_conf']['bee_vm']

    def get_bee_aws_conf(self):
        return self.__bee_conf['exec_env_conf']['bee_aws']

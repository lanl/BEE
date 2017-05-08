import json

class BeeConfigLoader(object):
    def __init__(self):
        self.__conf_file = open("./bee_config.json","r")
        self.__bee_conf = json.load(self.__conf_file)
        
    def get_job_conf(self):
        return self.__bee_conf['job_conf']

    def get_docker_conf(self):
        return self.__bee_conf['docker_conf']

    def get_bee_vm_conf(self):
        return self.__bee_conf['exec_env_conf']['bee_vm']

    def get_bee_aws_conf(self):
        return self.__bee_conf['exec_env_conf']['bee_aws']

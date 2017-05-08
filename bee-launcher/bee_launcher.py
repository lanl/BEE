#!/usr/bin/python
import Pyro4
from bee_config_loader import BeeConfigLoader
class BeeLauncher(object):
    def __init__(self):
        self.bldaemon = Pyro4.Proxy("PYRONAME:bee_launcher.daemon")

    def launch_bee_vm(self, hosts, job_conf, bee_vm_conf, docker_conf):
        print("BeeLauncher: send create cluster request")
        self.bldaemon.launch_bee_vm(hosts, job_conf, bee_vm_conf, docker_conf)

    def launch_bee_aws(self, job_conf, bee_aws_conf, docker_conf):
        self.bldaemon.launch_bee_aws(job_conf, bee_aws_conf, docker_conf)

    def start_cluster(self, name):
        self.bldaemon.start_cluster(name)

    def stop_cluster(self, name):
        self.bldaemon.stop_cluster(name)

    def remove_cluster(self, name):
        self.bldaemon.remove_cluster(name)

    def get_cluster_list(self):
        return self.bldaemon.get_cluster_list()

    def force_stop_all(self, hosts):
        self.bldaemon.force_stop_all(hosts)


def main():
    bee_luncher = BeeLauncher()
    bee_conf = BeeConfigLoader()
    job_conf = bee_conf.get_job_conf()
    docker_conf = bee_conf.get_docker_conf()
    exec_target = job_conf['exec_target']

    if exec_target == 'bee_aws':
        print("Launching BEE-AWS")
        bee_aws_conf = bee_conf.get_bee_aws_conf()
        bee_luncher.launch_bee_aws(job_conf, bee_aws_conf, docker_conf)
    elif exec_target == 'bee_vm':
        print("Launching BEE-VM")
        hosts = ["cn41", "cn42"]
        bee_vm_conf = bee_conf.get_bee_vm_conf()
        bee_luncher.launch_bee_vm(hosts, job_conf, bee_vm_conf, docker_conf)

if __name__ == "__main__":
    main()

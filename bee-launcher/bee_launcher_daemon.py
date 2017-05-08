#!/usr/bin/python
import Pyro4
from aws_launcher import AWSLauncher 
from bee_vm_launcher import BeeVMLauncher
@Pyro4.expose
class BeeLauncherDaemon(object):
    def __init__(self):
        print("Starting Bee Launcher Daemon..")
    
    def launch_bee_vm(self, hosts, job_conf, bee_aws_conf, docker_conf):
        print("Bee Launcher Daemon: received create cluster request")
        bee_vm_launcher = BeeVMLauncher(hosts, job_conf, bee_aws_conf, docker_conf)
        bee_vm_launcher.start()

    def launch_bee_aws(self, job_conf, bee_aws_conf, docker_conf):

        aws_launcher = AWSLauncher(job_conf, bee_aws_conf, docker_conf)
        aws_launcher.start()  

    def start_cluster(self, name):
        self.cluster_manager.start_cluster(name)

    def stop_cluster(self, name):
        self.cluster_manager.stop_cluster(name)

    def remove_cluster(self, name):
        self.cluster_manager.remove_cluster(name)

    def get_cluster_list(self):
        return self.cluster_manager.get_cluster_list()
    
    def force_stop_all(self, hosts):
        self.cluster_manager.force_stop_all(hosts)

def main():
    bldaemon = BeeLauncherDaemon()
    daemon = Pyro4.Daemon()
    bldaemon_uri = daemon.register(bldaemon)
    ns = Pyro4.locateNS()
    ns.register("bee_launcher.daemon", bldaemon_uri)
    print("Bee Launcher Daemon Started.")
    daemon.requestLoop()



if __name__=="__main__":
    main()

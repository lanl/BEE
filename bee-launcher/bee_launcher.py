#!/usr/bin/python
import Pyro4
from beefile_loader import BeefileLoader
import sys
import getopt
class BeeLauncher(object):
    def __init__(self):
        self.bldaemon = Pyro4.Proxy("PYRONAME:bee_launcher.daemon")

    def launch_bee_vm(self, job_conf, bee_vm_conf, docker_conf):
        #print("BeeLauncher: send create cluster request")
        self.bldaemon.launch_bee_vm(job_conf, bee_vm_conf, docker_conf)

    def launch_bee_aws(self, job_conf, bee_aws_conf, docker_conf):
        self.bldaemon.launch_bee_aws(job_conf, bee_aws_conf, docker_conf)

    def create_bee_aws_storage(self, efs_name, perf_mode = 'generalPurpose'):
        return self.bldaemon.create_bee_aws_storage(efs_name, perf_mode)


def main(argv):
    bee_luncher = BeeLauncher()
    beefile = ""
    try:
        opts, args = getopt.getopt(argv, "f:e:", ["beefile=", "efs="])
    except getopt.GetoptError:
        print("Using default Beefile.")
        beefile = "bee_config.json"

    for opt, arg in opts: 
        if opt in ("-f", "--beefile"):
            beefile = arg
        elif opt in ("-e", "--efs"):
            efs_id = bee_luncher.create_bee_aws_storage(arg)
            if efs_id == "-1":
                print("EFS name already exists!")
            else:
                print("EFS created: " + efs_id)
            exit()
        

    bee_conf = BeefileLoader(beefile)
    job_conf = bee_conf.get_job_conf()
    docker_conf = bee_conf.get_docker_conf()
    exec_target = job_conf['exec_target']

    if exec_target == 'bee_aws':
        print("Launching BEE-AWS")
        bee_aws_conf = bee_conf.get_bee_aws_conf()
        bee_luncher.launch_bee_aws(job_conf, bee_aws_conf, docker_conf)
    elif exec_target == 'bee_vm':
        print("Launching BEE-VM")
        bee_vm_conf = bee_conf.get_bee_vm_conf()
        bee_luncher.launch_bee_vm(job_conf, bee_vm_conf, docker_conf)

if __name__ == "__main__":
    main(sys.argv[1:])

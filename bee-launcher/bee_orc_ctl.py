#!/usr/bin/python
import Pyro4
from aws_launcher import AWSLauncher 
from bee_vm_launcher import BeeVMLauncher
import boto3

@Pyro4.expose
class BeeLauncherDaemon(object):
    def __init__(self):
        print("Starting Bee orchestration controller..")
        self.__bee_vm_jobs = []
        self.__bee_aws_jobs = []
        
    def launch_bee_vm(self, hosts, job_conf, bee_aws_conf, docker_conf):
        print("Bee orchestration controller: received job launching request")
        bee_vm_launcher = BeeVMLauncher(len(self.__bee_vm_jobs) + 1, hosts, job_conf, bee_aws_conf, docker_conf)
        self.__bee_vm_jobs.append(bee_vm_launcher)
        bee_vm_launcher.start()

    def launch_bee_aws(self, job_conf, bee_aws_conf, docker_conf):
        print("Bee orchestration controller: received job launching request")
        aws_launcher = AWSLauncher(len(self.__bee_aws_jobs) + 1, job_conf, bee_aws_conf, docker_conf)
        self.__bee_aws_jobs.append(aws_launcher)
        aws_launcher.start()  
    
    def create_bee_aws_storage(self, efs_name, perf_mode = 'generalPurpose'):
        print("Bee orchestration controller: received bee-aws storage creating request")
        if self.get_bee_efs_id(efs_name) != -1:
            print("EFS named " + efs_name + "already exist!")
            return  '-1'
        efs_client = boto3.client('efs')
        efs_client.create_file_system(CreationToken = efs_name, PerformanceMode = perf_mode)
        resp = efs_client.describe_file_systems(CreationToken = efs_name)
        efs_id = resp['FileSystems'][0]['FileSystemId']
        efs_client.create_tags(FileSystemId = efs_id,
                               Tags=[{'Key':'Name', 'Value':efs_name}])
        self.wait_bee_efs(efs_name)
        print('Created new BEE EFS:' + efs_id)
        return efs_id

    # Get the id of bee efs, if not exist, -1 is returned.                                                                                                 
    def get_bee_efs_id(self, efs_name):
        all_efss = boto3.client('efs').describe_file_systems()
        bee_efs_id = -1
        for efs in all_efss['FileSystems']:
            if efs['CreationToken'] == efs_name:
                bee_efs_id = efs['FileSystemId']
        return bee_efs_id

    def wait_bee_efs(self, efs_name):
        print("Wait for EFS to become available.")
        efs_client = boto3.client('efs')
        resp = efs_client.describe_file_systems(CreationToken = efs_name)
        state = resp['FileSystems'][0]['LifeCycleState']
        while state != 'available':
            resp = efs_client.describe_file_systems(CreationToken = efs_name)
            state = resp['FileSystems'][0]['LifeCycleState']

def main():
    bldaemon = BeeLauncherDaemon()
    daemon = Pyro4.Daemon()
    bldaemon_uri = daemon.register(bldaemon)
    ns = Pyro4.locateNS()
    ns.register("bee_launcher.daemon", bldaemon_uri)
    print("Bee orchestration controller started.")
    daemon.requestLoop()



if __name__=="__main__":
    main()

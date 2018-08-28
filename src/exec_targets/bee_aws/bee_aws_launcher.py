import boto3
import time
from docker import Docker
from bee_aws import BeeAWS 
import os
import getpass
from os.path import expanduser
from termcolor import colored, cprint
from threading import Thread
from threading import Event
from bee_task import BeeTask

class BeeAWSLauncher(BeeTask):
    def __init__(self, task_id, beefile):
        
        BeeTask.__init__(self)

        self.__platform = 'BEE-AWS'
        
        self.__current_status = 0 #Initializing

        self.ec2_client = boto3.client('ec2')
        self.efs_client = boto3.client('efs')
        
        # User configuration
        self.__task_conf = beefile['task_conf']
        self.__bee_aws_conf = beefile['exec_env_conf']['bee_aws']
        self.__docker_conf = beefile['docker_conf']
        self.__task_name = self.__task_conf['task_name']
        self.__task_id = task_id
        
        # AWS configuration
        self.__bee_aws_sgroup = '{}-{}-bee-aws-security-group'.format(getpass.getuser(), self.__task_name)
        self.__aws_sgroup_desciption = 'Security group for BEE-AWS instances.'
        self.__bee_aws_pgroup = '{}-{}-bee-aws-placement-group'.format(getpass.getuser(), self.__task_name)

        # System configuration
        self.__user_name = getpass.getuser()
        self.__bee_working_dir = expanduser("~") + "/.bee".format(self.__user_name)
        self.__tmp_dir = self.__bee_working_dir + "/tmp"

        # bee-aws list
        self.__bee_aws_list = []

        # Output color list
        self.__output_color_list = ["magenta", "cyan", "blue", "green", "red", "grey", "yellow"]
        #self.__output_color = self.__output_color_list[task_id % 7]
        self.__output_color = "cyan"

        # Events for workflow
        self.__begin_event = Event()
        self.__end_event = Event()
        self.__event_list = []

        self.__current_status = 1 # initialized

    def get_current_status(self):
        return self.__current_status

    def get_platform(self):
        return self.__platform

    def get_begin_event(self):
        return self.__begin_event

    def get_end_event(self):
        return self.__end_event

    def add_wait_event(self, new_event):
        self.__event_list.append(new_event)

    def run(self):
        self.launch()
    
    def construct_bee_security_groups(self):
        cprint('[' + self.__task_name + '] Construct security groups for BEE-AWS', self.__output_color)
        if self.get_bee_sg_id() == -1:
            cprint('[' + self.__task_name + '] Create Security Group: ' + self.__bee_aws_sgroup, self.__output_color)
            bee_sg_id = self.ec2_client.create_security_group(GroupName = self.__bee_aws_sgroup,
                                                              Description = self.__aws_sgroup_desciption)
            
            ec2 = boto3.resource('ec2')
            bee_sg = ec2.SecurityGroup(bee_sg_id['GroupId'])
            bee_sg.authorize_ingress(IpProtocol = 'tcp',
                                     FromPort = 22,
                                     ToPort = 22,
                                     CidrIp = '0.0.0.0/0')
            time.sleep(10)

    def construct_bee_placement_groups(self):
        cprint('[' + self.__task_name + '] Construct placement group for BEE-AWS', self.__output_color)
        if not self.is_bee_pg_exist():
            cprint('[' + self.__task_name + '] Create Placement Group: ' + self.__bee_aws_pgroup, self.__output_color)
            self.ec2_client.create_placement_group(GroupName = self.__bee_aws_pgroup,
                                                   Strategy='cluster')
            time.sleep(10)

    def configure_hostnames(self):
        cprint('[' + self.__task_name + '] Configure hostname for each node.', self.__output_color)
        for host1 in self.__bee_aws_list:
            for host2 in self.__bee_aws_list:
                host2.add_host_list(host1.private_ip, host1.hostname)


    def launch(self):
        self.terminate(clean = True)
        self.__current_status = 3 # Launching

        self.construct_bee_security_groups()
        self.construct_bee_placement_groups()

        # Start each worker
        num_of_nodes = int(self.__bee_aws_conf['num_of_nodes'])
        
        for i in range(0, num_of_nodes):
            hostname = ""
            if i == 0:
                hostname = "{}-{}-bee-master".format(getpass.getuser(), self.__task_name)
            else:
                hostname = "{}-{}-bee-worker{}".format(getpass.getuser(), self.__task_name, str(i).zfill(3))

            node = BeeAWS(self.__task_id, hostname, self.__bee_aws_conf, self.__task_conf,
                          self.__bee_aws_sgroup, self.__bee_aws_pgroup)
            node.start()
            self.__bee_aws_list.append(node)
        
        time.sleep(60)
        for i in range(0, num_of_nodes):
            self.__bee_aws_list[i].wait()
            self.__bee_aws_list[i].set_hostname()
        
        self.configure_hostnames()
        self.configure_efs()
        self.configure_dockers()
        self.wait_for_others()
        self.run_script()
        if self.__task_conf['terminate_after_exec']:
            self.terminate()
        
    def configure_dockers(self):
        for node in self.__bee_aws_list:
            docker = Docker(self.__docker_conf)
            node.add_docker_container(docker)
       
        master = self.__bee_aws_list[0]
        master.get_docker_img(self.__bee_aws_list)
        
        for node in self.__bee_aws_list:
            node.start_docker("/usr/sbin/sshd -D")
            node.docker_update_uid(1000)
            node.docker_update_gid(1000)

    def wait_for_others(self):
        self.__current_status = 2 # waiting
        # wait for other tasks
        for event in self.__event_list:
            event.wait()

    def run_script(self):
        self.__current_status = 4 # Running
        # set out flag as begin launching
        self.__begin_event.set()
        if self.__task_conf['batch_mode']:
            self.batch_run()
        else:
            self.general_run()
        self.__current_status = 5 # finished
        # set out flag after finished
        self.__end_event.set()

    def general_run(self):
        master = self.__bee_aws_list[0]

        for run_conf in self.__task_conf['general_run']:
            host_script_path = run_conf['script']
            vm_script_path = '/home/ubuntu/general_script.sh'

            docker_script_path = ''
            if (self.__docker_conf['docker_username'] == 'root'):
                docker_script_path = '/root/general_script.sh'
            else:
                docker_script_path = '/home/{}/general_script.sh'.format(self.__docker_conf['docker_username'])
                for bee_aws in self.__bee_aws_list:
                    bee_aws.docker_seq_run('cp -r /home/{}/.ssh /root/'.format(self.__docker_conf['docker_username']))
            
            master.copy_file(host_script_path, vm_script_path)
            master.docker_copy_file(vm_script_path, docker_script_path)
            master.docker_seq_run(docker_script_path, local_pfwd = run_conf['local_port_fwd'],
                                  remote_pfwd = run_conf['remote_port_fwd'], async = False)

        count = 0
        for run_conf in self.__task_conf['mpi_run']:
            host_script_path = run_conf['script']

            vm_script_path = '/home/ubuntu/mpi_script.sh'

            docker_script_path = ''
            hostfile_path = ''
            if (self.__docker_conf['docker_username'] == 'root'):
                docker_script_path = '/root/mpi_script.sh'
                hostfile_path = '/root/hostfile'
            else:
                docker_script_path = '/home/{}/mpi_script.sh'.format(self.__docker_conf['docker_username'])
                hostfile_path = '/home/{}/hostfile'.format(self.__docker_conf['docker_username'])
                for bee_aws in self.__bee_aws_list:
                    bee_aws.docker_seq_run('cp -r /home/{}/.ssh /root/'.format(self.__docker_conf['docker_username']))
		

            for bee_aws in self.__bee_aws_list:
                bee_aws.copy_file(host_script_path, vm_script_path)
                bee_aws.docker_copy_file(vm_script_path, docker_script_path)
            # Generate hostfile and copy to container                                                                    
            master.docker_make_hostfile(run_conf, self.__bee_aws_list, self.__tmp_dir)
            master.copy_file(self.__tmp_dir + '/hostfile', '/home/ubuntu me/ubuntu/hostfile', hostfile_path)
            # Run parallel script on all nodes
            master.docker_para_run(run_conf, docker_script_path, hostfile_path, local_pfwd = run_conf['local_port_fwd'],remote_pfwd = run_conf['remote_port_fwd'], async = False)



    def batch_run(self):
        run_conf_list = self.__task_conf['general_run']
        if len(run_conf_list) != len(self.__bee_aws_list):
            print("[Error] Scripts and BEE-VM not match in numbers!")
        popen_list = []
        count = 0
        for run_conf in run_conf_list:
            bee_aws = self.__bee_aws_list[count]
            count = count + 1
            host_script_path = run_conf['script']
            vm_script_path = '/home/ubuntu/general_script.sh'
            docker_script_path = '/home/{}/general_script.sh'.format(self.__docker_conf['docker_username'])
            bee_aws.copy_file(host_script_path, vm_script_path)
            bee_aws.docker_copy_file(vm_script_path, docker_script_path)
            p = bee_aws.docker_seq_run(docker_script_path, local_pfwd = run_conf['local_port_fwd'],
                                       remote_pfwd = run_conf['remote_port_fwd'], async = True)
            popen_list.append(p)
        for popen in popen_list:
            popen.wait()


    def configure_efs(self):
        efs_id = self.__bee_aws_conf['efs_id']
        resp = self.efs_client.describe_mount_targets(FileSystemId = efs_id)
        mts = set()
        for mt in resp['MountTargets']:
            mts.add(mt['SubnetId'])
        #print(mts)
        subnets = set()
        for node in self.__bee_aws_list:
            inst = node.getInstance()
            subnet_id = inst['NetworkInterfaces'][0]['SubnetId']
            
            if subnet_id not in subnets and subnet_id not in mts:
                
                resp = self.efs_client.create_mount_target(FileSystemId=efs_id,
                                                           SubnetId=subnet_id)
                cprint('[' + self.__task_name + '] Creating mount target:' + resp['IpAddress'], self.__output_color)
                
                mount_target_id = resp['MountTargetId']
                
                resp = self.efs_client.describe_mount_targets(MountTargetId = mount_target_id)
                cprint('[' + self.__task_name + '] Waiting for mount target to become available', self.__output_color)
                while resp['MountTargets'][0]['LifeCycleState'] != 'available':
                    time.sleep(1)
                    resp = self.efs_client.describe_mount_targets(MountTargetId = mount_target_id)
                    time.sleep(60)
                    subnets.add(subnet_id)
                    
            #node.create_shared_dir()
            time.sleep(10)
            node.mount_efs(efs_id)
            node.change_ownership()
                    
            

    def terminate(self, clean = False):
        print('Clear all')
        # Terminate all BEE-AWS instances
        bee_instance_ids = self.get_bee_instance_ids()
        num_of_all_existing = len(bee_instance_ids)
        if num_of_all_existing > 0:
            cprint('Terminate all existing instances', self.__output_color)
            cprint(bee_instance_ids, self.__output_color)
            self.ec2_client.terminate_instances(InstanceIds = bee_instance_ids)
            cprint('Waiting to terminate all instances', self.__output_color)
            while len(self.get_bee_instance_ids()) > 0:
                time.sleep(1)
                #print("\r{}/{} terminated".format(len(self.get_bee_instance_ids()), num_of_all_existing)),

        # Delete BEE-AWS security group
        if self.get_bee_sg_id() != -1:
            cprint('Delete existing security group:'+self.__bee_aws_sgroup, self.__output_color)
            self.ec2_client.delete_security_group(GroupName = self.__bee_aws_sgroup)
                        
        # Delete BEE-AWS placement group
        if self.is_bee_pg_exist():
            cprint('Delete existing placement group:'+self.__bee_aws_pgroup, self.__output_color)
            self.ec2_client.delete_placement_group(GroupName = self.__bee_aws_pgroup)
        if not clean:
            self.__current_status = 6 # terminated

    # Get all instance ids of bee
    def get_bee_instance_ids(self):
        resp = self.ec2_client.describe_instances()
        inst_ids = []
        for rsv in resp['Reservations']:
            for inst in rsv['Instances']:
                if inst['Placement']['GroupName'] == self.__bee_aws_pgroup and inst['State']['Name'] != 'terminated':
                    
                    inst_ids.append(inst['InstanceId'])
        return inst_ids
            
    # Get the id of bee security group, if not exist, -1 is returned.        
    def get_bee_sg_id(self):
        all_sgs = self.ec2_client.describe_security_groups()
        bee_security_group_id = -1
        for sg in all_sgs['SecurityGroups']:
            if sg['GroupName'] == self.__bee_aws_sgroup:
                #print('Security Group: bee-aws-security-group exists:' + sg['GroupId'])
                bee_security_group_id = sg['GroupId']                    
        return bee_security_group_id

    # Determine if bee placement group exists.
    def is_bee_pg_exist(self):
        all_pgs = self.ec2_client.describe_placement_groups()
        bee_placement_group_exist = False
        for pg in all_pgs['PlacementGroups']:
            if pg['GroupName'] == self.__bee_aws_pgroup:
                #print('Placement Group: bee-aws-placement-group exists')
                bee_placement_group_exist = True
                    
        return bee_placement_group_exist

    def get_mount_target_ids(self):
        bee_efs_id = self.get_bee_efs_id()
        resp = self.efs_client.describe_mount_targets(FileSystemId = bee_efs_id)
        mount_target_ids = []
        for mt in resp['MountTargets']:
            mount_target_ids.append(mt['MountTargetId'])
        
        return mount_target_ids
        

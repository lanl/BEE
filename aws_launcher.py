import boto3
import time
from docker import Docker
from bee_aws import BeeAWS 
import os

class AWSLauncher(object):
    def __init__(self, job_conf, bee_aws_conf, docker_conf):
        self.ec2_client = boto3.client('ec2')
        self.efs_client = boto3.client('efs')
        
        self.__job_conf = job_conf
        self.__bee_aws_conf = bee_aws_conf
        self.__docker_conf = docker_conf
        
        self.__bee_aws_sgroup = 'bee-aws-security-group'
        self.__aws_sgroup_desciption = 'Security group for BEE-AWS instances.'
        self.__bee_aws_pgroup = 'bee-aws-placement-group'
        self.__bee_aws_storage = 'bee-aws-storage'
        self.__bee_aws_list = []

        self.__user_name = os.getlogin()
        self.__bee_working_dir = "/home/{}/.bee".format(self.__user_name)
        self.__tmp_dir = self.__bee_working_dir + "/tmp"

    def construct_bee_security_groups(self):
        print('Construct security groups for BEE-AWS')
        if self.get_bee_sg_id() == -1:
            print('Create Security Group: bee-aws-security-group')
            bee_sg_id = self.ec2_client.create_security_group(GroupName = self.__bee_aws_sgroup,
                                                              Description = self.__aws_sgroup_desciption)
            
            ec2 = boto3.resource('ec2')
            bee_sg = ec2.SecurityGroup(bee_sg_id['GroupId'])
            bee_sg.authorize_ingress(IpProtocol = 'tcp',
                                     FromPort = 22,
                                     ToPort = 22,
                                     CidrIp = '0.0.0.0/0')

    def construct_bee_placement_groups(self):
        print('Construct placement group for BEE-AWS')
        
        if not self.is_bee_pg_exist():
            print('Create Placement Group: bee-aws-placement-group')
            self.ec2_client.create_placement_group(GroupName = self.__bee_aws_pgroup,
                                                   Strategy='cluster')
        

    def configure_hostnames(self):
        for host1 in self.__bee_aws_list:
            for host2 in self.__bee_aws_list:
                host2.add_host_list(host1.private_ip, host1.hostname)


    def start(self):

        self.clear_all()
        self.construct_bee_security_groups()
        self.construct_bee_placement_groups()

        # Start each workers
        num_of_nodes = int(self.__job_conf['num_of_nodes'])
        
        for i in range(0, num_of_nodes):
            hostname = ""
            if i == 0:
                hostname = "bee-master"
            else:
                hostname = "bee-worker{}".format(str(i).zfill(3))

            node = BeeAWS(hostname, self.__bee_aws_conf, self.__job_conf,
                          self.__bee_aws_sgroup, self.__bee_aws_pgroup)
            node.start()
            self.__bee_aws_list.append(node)
        
        time.sleep(90)
        for i in range(0, num_of_nodes):
            self.__bee_aws_list[i].wait()
            self.__bee_aws_list[i].set_hostname()
        
    
        
        self.configure_hostnames()
        self.configure_efs()
        self.configure_dockers()
        self.configure_run_script()
        

    def configure_dockers(self):
        for node in self.__bee_aws_list:
            docker = Docker(self.__docker_conf)
            node.add_docker_container(docker)
       
        master = self.__bee_aws_list[0]
        master.get_docker_img(self.__bee_aws_list)
        
        for node in self.__bee_aws_list:
            node.start_docker("/usr/sbin/sshd -D")
            #node.docker_update_uid(1000)
            #node.docker_update_gid(1000)

    def configure_run_script(self):
        seq_file = self.__job_conf['seq_run_script']
        para_file = self.__job_conf['para_run_script']
        for bee_aws in self.__bee_aws_list:
            bee_aws.copy_file(seq_file, '/home/ubuntu/seq_script.sh')
            bee_aws.docker_copy_file('/home/ubuntu/seq_script.sh', '/root/seq_script.sh')
            bee_aws.copy_file(para_file, '/home/ubuntu/para_script.sh')
            bee_aws.docker_copy_file('/home/ubuntu/para_script.sh', '/root/para_script.sh')

        # Generate hostfile and copy to container                                                                                                          
        self.__bee_aws_list[0].docker_make_hostfile(self.__bee_aws_list, self.__tmp_dir)
        self.__bee_aws_list[0].copy_file(self.__tmp_dir + '/hostfile', '/home/ubuntu/hostfile')
        self.__bee_aws_list[0].docker_copy_file('/home/ubuntu/hostfile', '/root/hostfile')
        
        # Run sequential script on master                                                                                                                  
        self.__bee_aws_list[0].docker_seq_run('/root/seq_script.sh')

        # Run parallel script on all nodes                                                                                                                 
        self.__bee_aws_list[0].docker_para_run('/root/para_script.sh', self.__bee_aws_list)

    def configure_efs(self):
        if self.get_bee_efs_id() == -1:
            self.efs_client.create_file_system(CreationToken=self.__bee_aws_storage, PerformanceMode='generalPurpose')
            
            
            resp = self.efs_client.describe_file_systems(CreationToken = self.__bee_aws_storage)
        
            efs_id = resp['FileSystems'][0]['FileSystemId']
            
            print('Created new BEE EFS:' + efs_id)


            self.wait_bee_efs()


            self.efs_client.create_tags(FileSystemId = efs_id,
                                        Tags=[{'Key':'Name', 'Value':self.__bee_aws_storage}])

        
            subnets = set()
            for node in self.__bee_aws_list:
                inst = node.getInstance()
                subnet_id = inst['NetworkInterfaces'][0]['SubnetId']
                
                if subnet_id not in subnets:
                    resp = self.efs_client.create_mount_target(FileSystemId=efs_id,
                                                               SubnetId=subnet_id)
                    print('Mount target:' + resp['IpAddress'])
                    mount_target_id = resp['MountTargetId']
                
                    resp = self.efs_client.describe_mount_targets(MountTargetId = mount_target_id)
                    print('Waiting for mount target to become available')
                    while resp['MountTargets'][0]['LifeCycleState'] != 'available':
                        time.sleep(1)
                        resp = self.efs_client.describe_mount_targets(MountTargetId = mount_target_id)
                    time.sleep(60)
                    subnets.add(subnet_id)

                node.create_shared_dir()
                node.mount_efs(efs_id)
                node.change_ownership()
            
            

    def clear_all(self):
        print('Clear all')
        # Terminate all BEE-AWS instances
        bee_instance_ids = self.get_bee_instance_ids()
        num_of_all_existing = len(bee_instance_ids)
        if num_of_all_existing > 0:
            print('Terminate all existing instances')
            print(bee_instance_ids)
            self.ec2_client.terminate_instances(InstanceIds = bee_instance_ids)
            print('Waiting to terminate all instances')
            while len(self.get_bee_instance_ids()) > 0:
                time.sleep(1)
                print("\r{}/{} terminated".format(len(self.get_bee_instance_ids()), num_of_all_existing)),

        # Delete BEE-AWS security group
        if self.get_bee_sg_id() != -1:
            print('Delete existing security group:'+self.__bee_aws_sgroup)
            self.ec2_client.delete_security_group(GroupName = self.__bee_aws_sgroup)
                        
        # Delete BEE-AWS placement group
        if self.is_bee_pg_exist():
            print('Delete existing placement group:'+self.__bee_aws_pgroup)
            self.ec2_client.delete_placement_group(GroupName = self.__bee_aws_pgroup)

        # Delete BEE-AWS storage
        bee_efs_id = self.get_bee_efs_id()
        if bee_efs_id != -1:
            mount_target_ids = self.get_mount_target_ids()
            for mount_target_id in mount_target_ids:
                print('Delete mount target:' + mount_target_id)
                self.efs_client.delete_mount_target(MountTargetId = mount_target_id)
            while len(self.get_mount_target_ids()) != 0:
                time.sleep(1)
                continue
            print('Delete efs:'+bee_efs_id)
            self.efs_client.delete_file_system(FileSystemId = bee_efs_id)
            

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

    # Get the id of bee efs, if not exist, -1 is returned.
    def get_bee_efs_id(self):
        all_efss = self.efs_client.describe_file_systems()
        bee_efs_id = -1
        for efs in all_efss['FileSystems']:
            if efs['CreationToken'] == self.__bee_aws_storage:
                bee_efs_id = efs['FileSystemId']
        return bee_efs_id

    def get_mount_target_ids(self):
        bee_efs_id = self.get_bee_efs_id()
        resp = self.efs_client.describe_mount_targets(FileSystemId = bee_efs_id)
        mount_target_ids = []
        for mt in resp['MountTargets']:
            mount_target_ids.append(mt['MountTargetId'])
        
        return mount_target_ids
        


    def wait_bee_efs(self):
        print("Wait for EFS to become available.")
        resp = self.efs_client.describe_file_systems(CreationToken = self.__bee_aws_storage)
        state = resp['FileSystems'][0]['LifeCycleState']
        while state != 'available':
            resp = self.efs_client.describe_file_systems(CreationToken = self.__bee_aws_storage)
            state = resp['FileSystems'][0]['LifeCycleState']

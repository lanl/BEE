import os
import getpass
import subprocess
import time
from os.path import expanduser
import getpass
import sys


from docker import Docker
from termcolor import colored, cprint
from threading import Thread
from threading import Event
from bee_task import BeeTask
from bee_os import BeeOS
from docker import Docker

from keystoneauth1 import loading
from keystoneauth1 import session
from keystoneauth1.identity import v2

from glanceclient import Client as glanceClient
from novaclient.client import Client as novaClient
from neutronclient.v2_0.client import Client as neutronClient

class BeeOSLauncher(BeeTask):

    def __init__(self, task_id, beefile = "", scalability_test = False):

        BeeTask.__init__(self)

        self.__platform = 'BEE-OpenStack'

        self.__current_status = 0 #Initializing

        # User configuration
        self.__task_conf = beefile['task_conf']
        self.__bee_os_conf = beefile['exec_env_conf']['bee_os']
        self.__docker_conf = beefile['docker_conf']
        self.__task_name = self.__task_conf['task_name']
        self.__task_id = task_id
        self.__reservation_id = self.__bee_os_conf['reservation_id']

        # OS configuration
        self.__bee_os_sgroup = '{}-{}-bee-os-security-group'.format(getpass.getuser(), self.__task_name)
        self.__ssh_key = '{}-{}-bee-os-sshkey'.format(getpass.getuser(), self.__task_name)
        self.__stack_name = '{}-{}-bee-os-stack'.format(getpass.getuser(), self.__task_name)


        self.__key_path = expanduser("~") + '/.bee/ssh_key/id_rsa'
        self.__ssh_dir = expanduser("~") + '/.bee/ssh_key'
        self.__bee_working_dir = expanduser("~") + "/.bee"
        self.__tmp_dir = self.__bee_working_dir + "/tmp"

        self.os_key = ""

        self.nova = novaClient('2', 
                               os.environ['OS_USERNAME'], 
                               os.environ['OS_PASSWORD'], 
                               os.environ['OS_TENANT_ID'], 
                               os.environ['OS_AUTH_URL'])

        self.__bee_os_list = []
        self.__output_color = "cyan"


        # Events for workflow
        self.__begin_event = Event()
        self.__end_event = Event()
        self.__event_list = []

        self.__scalability_test = scalability_test

        self.__current_status = 1 # initialized

    def run(self):
        self.launch()

    def launch(self):
        self.__current_status = 3 # Launching
        self.terminate()
        self.create_key()
        self.launch_stack()
        self.wait_for_nodes()
        self.get_master_node()
        self.get_worker_nodes()
        self.setup_sshkey()
        self.setup_sshconfig()
        self.setup_hostname()
        self.setup_hostfile()
        self.setup_storage()
        self.add_docker()
        self.__bee_os_list[0].parallel_run(['hostname'], self.__bee_os_list)
        self.get_docker_img()
        self.start_docker()
        self.__current_status = 2 # waiting
        self.wait_for_others()
        self.__current_status = 4 # Running
        if (self.__scalability_test):
            self.scalability_test_run()
        else:
            self.general_run()
        self.__current_status = 5 # finished

    def setup_storage(self):
        # set nfs on master
        self.__bee_os_list[0].set_nfs_master();
        master_private_ip = self.__bee_os_list[0].private_ip
        for i in range(1, len(self.__bee_os_list)):
            worker = self.__bee_os_list[i]
            worker.set_nfs_worker(master_private_ip)


    def wait_for_others(self):
        # wait for other tasks
        for event in self.__event_list:
            event.wait()

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


    def terminate(self):
        cprint('[' + self.__task_name + '] Clean old keys and stacks.', self.__output_color)
        for existing_key in self.nova.keypairs.list():
            if (existing_key.id == self.__ssh_key):
                self.nova.keypairs.delete(key = self.__ssh_key)
        
        cmd = ['openstack stack delete -y {}'.format(self.__stack_name)]
        print(" ".join(cmd))
        subprocess.call(" ".join(cmd), shell=True)
        time.sleep(60)

    def create_key(self):
        cprint('[' + self.__task_name + '] Create new ssh key.', self.__output_color)
        f = open(expanduser("~") + '/.bee/ssh_key/id_rsa.pub','r')
        publickey = f.readline()[:-1]
        self.os_key = self.nova.keypairs.create(self.__ssh_key, publickey)
        f.close()

    def launch_stack(self):
        cprint('[' + self.__task_name + '] Launch stack', self.__output_color)
        curr_dir = os.path.dirname(os.path.abspath(__file__))
        hot_template_dir = curr_dir + "/bee_hot"
        cmd = [ "openstack " +
                "stack create " + 
                "-t {} ".format(hot_template_dir) + 
                "--parameter bee_workers_count={} ".format(int(self.__bee_os_conf['num_of_nodes']) - 1) +
                "--parameter key_name={} ".format(self.__ssh_key) +
                "--parameter reservation_id={} ".format(self.__reservation_id) +
                "--parameter security_group_name={} ".format(self.__bee_os_sgroup) +
                "{}".format(self.__stack_name)]
        print(" ".join(cmd))
        subprocess.call(cmd, shell=True)

    def launch_stack_storage(self):
        cprint('[' + self.__task_name + '] Launch stack', self.__output_color)
        curr_dir = os.path.dirname(os.path.abspath(__file__))
        hot_template_dir = curr_dir + "/bee_hot_storage"
        cmd = [ "openstack " +
                "stack create " + 
                "-t {} ".format(hot_template_dir) + 
                "--parameter bee_workers_count={} ".format(int(self.__bee_os_conf['num_of_nodes']) - 1) +
                "--parameter key_name={} ".format(self.__ssh_key) +
                "--parameter reservation_id={} ".format(self.__reservation_id) +
                "--parameter security_group_name={} ".format(self.__bee_os_sgroup) +
                "{}".format(self.__stack_name)]
        print(" ".join(cmd))
        subprocess.call(cmd, shell=True)
        
    def get_active_node(self):
        active_nodes = []
        all_active_servers = self.nova.servers.list(search_opts={'status': 'ACTIVE'})
        for server in all_active_servers:
            sgs = server.list_security_group()
            for sg in sgs:
                if (sg.to_dict()['name'] == self.__bee_os_sgroup):
                    active_nodes.append(server)
        return active_nodes

    def wait_for_nodes(self):
        cprint('[' + self.__task_name + '] Waiting for all nodes to become active.', self.__output_color)
        counter = 0
        while (len(self.get_active_node()) != int(self.__bee_os_conf['num_of_nodes'])):
            time.sleep(5)
            counter += 1
            # output something to avoid accident termination by Travis CI
            if (counter % 30 == 0):
                sys.stdout.write('.')
                sys.stdout.flush()
        print(" ")
        cprint('[' + self.__task_name + '] All nodes are active, wait for networks to become available.', self.__output_color)
        time.sleep(200)
        cprint('[' + self.__task_name + '] Start BEE configuration.', self.__output_color)
        

    def get_master_node(self):
        cprint('[' + self.__task_name + '] Find the ip for the master node.', self.__output_color)
        all_servers = self.nova.servers.list()
        rank = 0
        for server in all_servers:
            sgs = server.list_security_group()
            for sg in sgs:
                if (sg.to_dict()['name'] == self.__bee_os_sgroup):
                    ip_list = server.networks['sharednet1']
                    if (len(ip_list) == 2):
                        hostname = "{}-bee-master".format(self.__task_name)
                        master = BeeOS(self.__task_id, 
                                       hostname, 
                                       0, 
                                       self.__task_conf, 
                                       self.__bee_os_conf, 
                                       self.__key_path,
                                       ip_list[0],
                                       ip_list[1])
                        self.__bee_os_list.insert(0, master)
                        print('find master with ip: ' + ip_list[0] + ", " + ip_list[1])
    def get_master_ip(self):
        return self.__bee_os_list[0].master_public_ip

    def get_worker_nodes(self):
        cprint('[' + self.__task_name + '] Find the ip for worker nodes.', self.__output_color)
        all_servers = self.nova.servers.list()
        rank = 1
        for server in all_servers:
            sgs = server.list_security_group()
            for sg in sgs:
                if (sg.to_dict()['name'] == self.__bee_os_sgroup):
                    ip_list = server.networks['sharednet1']
                    if (len(ip_list) == 1):
                        hostname = "{}-bee-worker{}".format(self.__task_name, str(rank).zfill(3))
                        worker = BeeOS(self.__task_id, 
                                       hostname, 
                                       rank, 
                                       self.__task_conf, 
                                       self.__bee_os_conf, 
                                       self.__key_path,
                                       ip_list[0],
                                       self.__bee_os_list[0].master_public_ip,
                                       self.__bee_os_list[0])
                        self.__bee_os_list.append(worker)
                        print('find worker with ip: ' + ip_list[0])
            rank = rank + 1


    def setup_sshkey(self):
        cprint('[' + self.__task_name + '] Copy ssh key into each node.', self.__output_color)
        self.__bee_os_list[0].copy_to_master(self.__ssh_dir + '/id_rsa', '/home/cc/.ssh/id_rsa')
        for i in range(1, len(self.__bee_os_list)):
            self.__bee_os_list[0].copy_to_worker('/home/cc/.ssh/id_rsa', '/home/cc/.ssh/id_rsa', self.__bee_os_list[i])

    def setup_sshconfig(self):
        cprint('[' + self.__task_name + '] Copy ssh config into each node.', self.__output_color)
        self.__bee_os_list[0].copy_to_master(self.__ssh_dir + '/config', '/home/cc/.ssh/config')
        for i in range(1, len(self.__bee_os_list)):
            self.__bee_os_list[0].copy_to_worker('/home/cc/.ssh/config', '/home/cc/.ssh/config', self.__bee_os_list[i])

    def setup_hostname(self):
        cprint('[' + self.__task_name + '] Setup hostname for each node.', self.__output_color)
        for bee_os in self.__bee_os_list:
            bee_os.set_hostname()

    def setup_hostfile(self):
        cprint('[' + self.__task_name + '] Setup /etc/hosts file for each node.', self.__output_color)
        # Setup hosts file
        for node1 in self.__bee_os_list:
            for node2 in self.__bee_os_list:
                node2.add_host_list(node1.get_ip(), node1.get_hostname())



    def add_docker(self):
        cprint('[' + self.__task_name + '] Initialize docker', self.__output_color)
        for bee_os in self.__bee_os_list:
            docker = Docker(self.__docker_conf)
            docker.set_shared_dir('/exports/host_share/')
            bee_os.add_docker_container(docker)

    def get_docker_img(self):
        cprint('[' + self.__task_name + '] Pull docker images.', self.__output_color)
        self.__bee_os_list[0].get_docker_img(self.__bee_os_list)

    def start_docker(self):
        cprint('[' + self.__task_name + '] Start docker on each node', self.__output_color)
        for bee_os in self.__bee_os_list:
            bee_os.start_docker("/usr/sbin/sshd -D")


    def general_run(self):
        cprint('[' + self.__task_name + '] Execute run scripts.', self.__output_color)
        
        # General sequential script
        master = self.__bee_os_list[0]
        for run_conf in self.__task_conf['general_run']:
            local_script_path = run_conf['script']
            node_script_path = '/exports/host_share/general_script.sh'
            
            docker_script_path = ''
            if (self.__docker_conf['docker_username'] == 'root'):
                docker_script_path = '/root/general_script.sh'
            else:
                docker_script_path = '/home/{}/general_script.sh'.format(self.__docker_conf['docker_username'])
                for bee_os in self.__bee_os_list:
                    bee_os.docker_seq_run('cp -r /home/{}/.ssh /root/'.format(self.__docker_conf['docker_username']))
            
            master.copy_to_master(local_script_path, node_script_path)
            master.set_file_permssion(node_script_path)
            master.docker_copy_file(node_script_path, docker_script_path)
            master.docker_seq_run(docker_script_path, local_pfwd = run_conf['local_port_fwd'],
                                  remote_pfwd = run_conf['remote_port_fwd'], async = False)

        for run_conf in self.__task_conf['mpi_run']:
            local_script_path = run_conf['script']
            node_script_path = '/exports/host_share/mpi_script.sh'
            
            docker_script_path = ''
            hostfile_path = ''
            if (self.__docker_conf['docker_username'] == 'root'):
                docker_script_path = '/root/mpi_script.sh'
                hostfile_path = '/root/hostfile'
            else:
                docker_script_path = '/home/{}/mpi_script.sh'.format(self.__docker_conf['docker_username'])
                hostfile_path = '/home/{}/hostfile'.format(self.__docker_conf['docker_username'])
                for bee_os in self.__bee_os_list:
                    bee_os.docker_seq_run('cp -r /home/{}/.ssh /root/'.format(self.__docker_conf['docker_username']))
			
            
            master.copy_to_master(local_script_path, node_script_path)
            master.set_file_permssion(node_script_path)
            for bee_os in self.__bee_os_list:
                bee_os.docker_copy_file(node_script_path, docker_script_path)
		
            # Generate hostfile and copy to container
            master.docker_make_hostfile(run_conf, self.__bee_os_list, self.__tmp_dir)
            master.copy_to_master(self.__tmp_dir + '/hostfile', '/home/cc/hostfile')
            master.docker_copy_file('/home/cc/hostfile', hostfile_path)    
            # Run parallel script on all nodes
            master.docker_para_run(run_conf, 
                                   docker_script_path, 
                                   hostfile_path, 
                                   local_pfwd = run_conf['local_port_fwd'],
                                   remote_pfwd = run_conf['remote_port_fwd'],
                                   async = False)


    def scalability_test_run(self):
        cprint('[' + self.__task_name + '] Start scalability test.', self.__output_color)
        master = self.__bee_os_list[0]

        for run_conf in self.__task_conf['mpi_run']:
            local_script_path = run_conf['script']
            node_script_path = '/exports/host_share/mpi_script.sh'

            docker_script_path = ''
            hostfile_path = ''
            if (self.__docker_conf['docker_username'] == 'root'):
                docker_script_path = '/root/mpi_script.sh'
                hostfile_path = '/root/hostfile'
            else:
                docker_script_path = '/home/{}/mpi_script.sh'.format(self.__docker_conf['docker_username'])
                hostfile_path = '/home/{}/hostfile'.format(self.__docker_conf['docker_username'])
                for bee_os in self.__bee_os_list:
                    bee_os.docker_seq_run('cp -r /home/{}/.ssh /root/'.format(self.__docker_conf['docker_username']))

            master.copy_to_master(local_script_path, node_script_path)
            for bee_os in self.__bee_os_list:
                bee_os.docker_copy_file(node_script_path, docker_script_path)

            # Generate hostfile and copy to container
            master.docker_make_hostfile(run_conf, self.__bee_os_list, self.__tmp_dir)
            master.copy_to_master(self.__tmp_dir + '/hostfile', '/home/cc/hostfile')
            master.docker_copy_file('/home/cc/hostfile', hostfile_path)
            master.docker_para_run_scalability_test(run_conf, 
                                                    docker_script_path, 
                                                    hostfile_path,
                                                    local_pfwd = run_conf['local_port_fwd'],
                                                    remote_pfwd = run_conf['remote_port_fwd'], 
                                                    async = False)

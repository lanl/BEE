import os
import subprocess
import time
from os.path import expanduser

from docker import Docker
from termcolor import colored, cprint
from threading import Thread
from threading import Event
from bee_task import BeeTask
from bee_os import BeeOS

from keystoneauth1 import loading
from keystoneauth1 import session
from keystoneauth1.identity import v2

from glanceclient import Client as glanceClient
from novaclient.client import Client as novaClient
from neutronclient.v2_0.client import Client as neutronClient

class BeeOSLauncher(BeeTask):

    def __init__(self, task_id, beefile):

        BeeTask.__init__(self)
        # User configuration
        self.__task_conf = beefile['task_conf']
        self.__bee_os_conf = beefile['exec_env_conf']['bee_os']
        self.__docker_conf = beefile['docker_conf']
        self.__task_name = self.__task_conf['task_name']
        self.__task_id = task_id

        # OS configuration
        self.__bee_os_sgroup = '{}-{}-bee-os-security-group'.format(os.getlogin(), self.__task_name)
        self.__ssh_key = '{}-{}-bee-os-sshkey'.format(os.getlogin(), self.__task_name)
        self.__reservation_id = 'e9bb49a6-dedc-4229-94ab-a23e46501645'
        self.__stack_name = '{}-{}-bee-os-stack'.format(os.getlogin(), self.__task_name)

        self.__key_path = expanduser("~") + '/.bee/ssh_key/id_rsa'
        self.__ssh_dir = expanduser("~") + '/.bee/ssh_key'

        self.os_key = ""

        # Authentication
        # auth = v2.Password(username = os.environ['OS_USERNAME'], 
        #                    password = os.environ['OS_PASSWORD'], 
        #                    tenant_name = os.environ['OS_TENANT_NAME'], 
        #                    auth_url = os.environ['OS_AUTH_URL'])

        # auth = v2.Password(username = 'cjy7117',
        #            password = 'Wait4aTrain7!',
        #            tenant_name = 'CH-819321',
        #            auth_url = 'https://chi.tacc.chameleoncloud.org:5000/v2.0')
        
        # self.session = session.Session(auth = auth)
        
        # self.glance = glanceClient('2', session = self.session)

        # self.nova = novaClient('2', session = self.session)

        # self.neutron = neutronClient(session = self.session)

        self.nova = novaClient('2', 
                                  'cjy7117', 
                                  'Wait4aTrain7!', 
                                  '3dbec77dc346466380d53adf7d39753b', 
                                  'https://chi.uc.chameleoncloud.org:5000')

        self.__bee_os_list = []

    def run(self):
        self.launch()


    def launch(self):
        self.clean()
        self.create_key()
        self.launch_stack()
        #self.get_master_node()
        #self.get_worker_nodes()
        #self.setup_sshkey()
        #self.setup_hostfile()
        #f = open(expanduser("~") + '/.bee/ssh_key/id_rsa.pub','r')
        #publickey = f.readline()[:-1]
        #keypair = nova.keypairs.create('bee-key', publickey)
        #f.close()


        # flavors = self.nova.flavors.list()
        # print (flavors)
        # f = flavors[0]

        #images = self.glance.images.list()
        #for image in images:
        #   print image

        # i = self.glance.images.get('10c1c632-1c4d-4c9d-bdd8-7938eeba9f14')

        # print(i)
        #k = self.nova.keypairs.create(name = 'bee-key')        

        # self.nova.servers.create(name = 'bee-os',
        #                          images = i,
        #                          flavor = f,
        #                          scheduler_hints = {'reservation': 'ac2cd341-cf88-4238-b45a-50fab07de465'},
        #                          key_name = 'bee-key'
        #                          )


    def clean(self):
        self.nova.keypairs.delete(key = self.__ssh_key)

    def create_key(self):
        f = open(expanduser("~") + '/.bee/ssh_key/id_rsa.pub','r')
        publickey = f.readline()[:-1]
        self.os_key = self.nova.keypairs.create(self.__ssh_key, publickey)
        f.close()

    def launch_stack(self):
        curr_dir = os.path.dirname(os.path.abspath(__file__))
        hot_template_dir = curr_dir + "/bee_hot"
        cmd = ["stack",
                    "create -t {}".format(hot_template_dir),
                    "--parameter bee_workers_count={}".format(self.__bee_os_conf['num_of_nodes']),
                    "--parameter key_name={}".format(self.__ssh_key),
                    "--parameter reservation_id={}".format(self.__reservation_id),
                    "--parameter security_group_name={}".format(self.__bee_os_sgroup),
                    "{}".format(self.__stack_name)]
        print(" ".join(cmd))
        subprocess.call(cmd)

        time.sleep(300)

    def get_master_node(self):
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

    def get_worker_nodes(self):
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
            rank = rank + 1


    def setup_sshkey(self):
        self.__bee_os_list[0].copy_to_master(self.__ssh_dir + '/id_rsa', '/home/cc/.ssh/id_rsa')
        for i in range(1, len(self.__bee_os_list)):
            self.__bee_os_list[0].copy_to_worker('/home/cc/.ssh/id_rsa', '/home/cc/.ssh/id_rsa', self.__bee_os_list[i])

    def setup_hostfile(self):
        # Setup hosts file
        for node1 in self.__bee_os_list:
            for node2 in self.__bee_os_list:
                node2.add_host_list(node1.get_ip(), node1.get_hostname())


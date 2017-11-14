import os

from docker import Docker
from termcolor import colored, cprint
from threading import Thread
from threading import Event
from bee_task import BeeTask

from keystoneauth1 import loading
from keystoneauth1 import session
from keystoneauth1.identity import v2

from glanceclient import Client as glanceClient
from novaclient.client import Client as novaClient
from neutronclient.v2_0.client import Client as neutronClient

class BeeOSLauncher(BeeTask):

    def __init__(self, task_id, beefile):

        BeeTask.__init__(self)
        # Authentication
        # auth = v2.Password(username = os.environ['OS_USERNAME'], 
        #                    password = os.environ['OS_PASSWORD'], 
        #                    tenant_name = os.environ['OS_TENANT_NAME'], 
        #                    auth_url = os.environ['OS_AUTH_URL'])

        auth = v2.Password(username = 'cjy7117',
                   password = 'Wait4aTrain7!',
                   tenant_name = 'CH-819321',
                   auth_url = 'https://chi.tacc.chameleoncloud.org:5000/v2.0')
        
        self.session = session.Session(auth = auth)
        
        self.glance = glanceClient('2', session = self.session)

        self.nova = novaClient('2', session = self.session)

        self.neutron = neutronClient(session = self.session)


    def run(self):
        self.launch()


    def launch(self):


        #f = open(expanduser("~") + '/.bee/ssh_key/id_rsa.pub','r')
        #publickey = f.readline()[:-1]
        #keypair = nova.keypairs.create('bee-key', publickey)
        #f.close()


        flavors = self.nova.flavors.list()
        print (flavors)
        f = flavors[0]

        #images = self.glance.images.list()
        #for image in images:
        #   print image

        i = self.glance.images.get('10c1c632-1c4d-4c9d-bdd8-7938eeba9f14')

        print(i)
        #k = self.nova.keypairs.create(name = 'bee-key')        

        self.nova.servers.create(name = 'bee-os',
                                 images = i,
                                 flavor = f,
                                 scheduler_hints = {'reservation': 'ac2cd341-cf88-4238-b45a-50fab07de465'},
                                 key_name = 'bee-key'
                                 )

        


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

class BeeOSLauncher(object):

	def __init__(self, task_id, beefile):
	    # Authentication
	    auth = v2.Password(username = 'cjy7117',
	                   password = 'Wait4aTrain7!',
	                   tenant_name = 'CH-819321',
	                   auth_url = 'https://chi.tacc.chameleoncloud.org:5000/v2.0')
	    
	    self.session = session.Session(auth = auth)
	    
	    self.glance = glanceClient('2', session = session)

	    self.nova = novaClient('2', session = session) 

	    self.neutron = neutronClient(session = sess)


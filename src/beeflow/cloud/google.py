"""Google provider code."""
import base64
import googleapiclient.discovery
import time

import beeflow.cloud.provider as provider
import beeflow.cloud.constants as constants


PREFIX = 'googlenode'
# Using Debian 10 as the base
SRC_IMAGE = 'https://www.googleapis.com/compute/v1/projects/debian-cloud/global/images/family/debian-10'
DISK_SIZE_GB = 10


class GoogleProvider(provider.Provider):
    """Google provider class."""

    def __init__(self, project, zone, **kwargs):
        """Google provider constructor."""
        # Set defaults here for now
        self._project = project
        self._zone = zone
        self._api = googleapiclient.discovery.build('compute', 'v1')
        self._nodes = {}

    def create_node(self, node_name, startup_script, ext_ip=False):
        """Create a node."""
        # name = f'{PREFIX}-{len(self._nodes)}'
        # TODO: Check that the node doesn't exist by using the API
        assert node_name not in self._nodes

        # TODO: Set correct machine type
        machine_type = 'n1-standard-1'
        machine_str = 'zones/%s/machineTypes/%s' % (self._zone, machine_type)
        config = {
            'name': node_name,
            'machineType': machine_str,

            'disks': [
                {
                    # Set the boot disk
                    'boot': True,
                    'autoDelete': True,
                    'initializeParams': {
                        # Set the source image and disk size
                        'sourceImage': SRC_IMAGE,
                        'diskSizeGb': DISK_SIZE_GB,
                    },
                }
            ],

            # TODO: Internal IP addressing/internal network
            'networkInterfaces': [
                {
                    # Public NAT IP
                    # TODO: This should be added only if ext_ip is True
                    'network': 'global/networks/default',
                    'accessConfigs': [
                        {
                            'type': 'ONE_TO_ONE_NAT',
                            'name': 'External NAT',
                        },
                    ]
                }
            ],

            'metadata': {
                'items': [
                    {
                        'key': 'startup-script',
                        'value': startup_script,
                    },
                ],
            },
        }

        res = self._api.instances().insert(project=self._project,
                                           zone=self._zone,
                                           body=config).execute()

        time.sleep(2)
        instance = self._api.instances().get(instance=node_name,
                                             project=self._project,
                                             zone=self._zone).execute()

        self._nodes[node_name] = instance

    def wait(self):
        """Wait for complete setup."""
        # Wait for two minutes -- this is arbitrary and should probably be user configurable
        time.sleep(100)

    def get_ext_ip_addr(self, node_name):
        """Get the external IP of this node (or None if no IP)."""
        res = self._api.instances().get(instance=node_name,
                                        project=self._project,
                                        zone=self._zone).execute()
        try:
            return res['networkInterfaces'][0]['accessConfigs'][0]['natIP']
        except (IndexError, KeyError):
            return None

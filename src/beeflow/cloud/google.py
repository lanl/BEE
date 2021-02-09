"""Google provider code."""
import base64
import googleapiclient.discovery

import beeflow.clouse.provider as provider


PREFIX = 'googlenode'
# Using Debian 10 as the base
SRC_IMAGE = 'https://www.googleapis.com/compute/v1/projects/debian-cloud/global/images/family/debian-10'
DISK_SIZE_GB = 10


class GoogleProvider(provider.Provider):
    """Google provider class."""

    def __init__(self):
        """Google provider constructor."""
        # Set defaults here for now
        self._project = 'bee-kent'
        self._zone = 'us-central1-f'
        self._api = googleapiclient.discovery.build('compute', 'v1')
        self._nodes = {}

    def create_node(self, ram_per_vcpu, vcpu_per_node, ext_ip):
        """Create a node."""
        name = f'{PREFIX}-{len(self._nodes)}'
        assert name not in self._nodes

        # TODO: Generate proper startup script
        startup_script = '#!/bin/sh\n'

        # TODO: Set correct machine type
        machine_type = 'n1-standard-1'
        machine_str = 'zones/%s/machineTypes/%s' % (self._zone, machine_type)
        config = {
            'name': name,
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
        instance = self._api.instance().get(instance=name,
                                            project=self._project,
                                            zone=self._zone).execute()

        self._nodes[name] = instance

        return instance

    def wait(self):
        """Wait for complete setup."""
        # TODO

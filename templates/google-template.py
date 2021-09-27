# machine_type = 'n1-standard-1'

SRC_IMAGE = 'https://www.googleapis.com/compute/v1/projects/debian-cloud/global/images/family/debian-10'
# DISK_SIZE_GB = 10


# TODO: Some of these arguments, like machine_type should be set by default in this template
def setup(template_api, node_name, startup_script=None,
          machine_type='n1-standard-1', src_image=SRC_IMAGE, disk_size_gb=10,
          **kwargs):
    """Create a google node config and return it."""
    items = []

    # Read in the startup_script if there is one
    if startup_script is not None:
        with open(startup_script) as fp:
            contents = fp.read()
        for key in kwargs:
            contents = contents.replace(f'${key.upper()}', kwargs[key])
        items.append({'key': 'startup-script', 'value': contents})

    # TODO: Internal IP addressing/internal network
    machine_str = 'zones/%s/machineTypes/%s' % (template_api.zone, machine_type)
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
                    'sourceImage': src_image,
                    'diskSizeGb': disk_size_gb,
                },
            }
        ],

        'networkInterfaces': [
            {
                # Public NAT IP
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
            'items': items,
        },
    }
    # Create the node
    template_api.create_node(config)

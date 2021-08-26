
import beeflow.cloud.google as google
import beeflow.cloud.chameleoncloud as chameleoncloud
import beeflow.cloud.openstack as openstack
import beeflow.cloud.provider as provider

from beeflow.cloud.cloud import CloudError
#from beeflow.cloud.cloud_info import CloudInfo
from beeflow.cloud.constants import *


providers = {
    'google': google.GoogleProvider,
    'chameleoncloud': chameleoncloud.ChameleoncloudProvider,
    'openstack': openstack.OpenstackProvider,
    'mock': provider.MockProvider,  # Provider to be used for testing
}


def get_provider(name, **kwargs):
    """Return a Provider object for the given provider."""
    if name in providers:
        return providers[name](**kwargs)

    raise RuntimeError('Invalid provider "%s"' % name)

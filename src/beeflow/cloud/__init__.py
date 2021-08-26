
from beeflow.cloud import chameleoncloud
from beeflow.cloud import openstack
from beeflow.cloud import provider
from beeflow.cloud import google
from beeflow.cloud.constants import BEE_USER


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

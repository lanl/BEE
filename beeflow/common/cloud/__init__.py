"""Cloud init module."""
from beeflow.common.cloud import chameleoncloud
from beeflow.common.cloud import openstack
from beeflow.common.cloud import provider
from beeflow.common.cloud import google
from beeflow.common.cloud.constants import BEE_USER
from beeflow.common.cloud.cloud import CloudError


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

    raise RuntimeError(f'Invalid provider "{name}"')
# Ignore W0611: These are meant to be used by external code
# pylama:ignore=W0611

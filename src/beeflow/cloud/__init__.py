
import beeflow.cloud.google as google
import beeflow.cloud.chameleon as chameleon
import beeflow.cloud.provider as provider

from beeflow.cloud.cloud import CloudError
#from beeflow.cloud.cloud_info import CloudInfo
from beeflow.cloud.constants import *


providers = {
    'Google': google.GoogleProvider,
    'Chameleon': chameleon.ChameleonProvider,
    'Mock': provider.MockProvider,  # Provider to be used for testing
}


def get_provider(name, **kwargs):
    """Return a Provider object for the given provider."""
    if name in providers:
        return providers[name](**kwargs)

    raise RuntimeError('Invalid provider "%s"' % name)

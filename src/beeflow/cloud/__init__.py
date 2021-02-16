
import beeflow.cloud.google as google
import beeflow.cloud.provider as provider

from beeflow.cloud.cloud import Cloud
from beeflow.cloud.constants import *


providers = {
    'Google': google.GoogleProvider,
    'Mock': provider.MockProvider,  # Provider to be used for testing
}


def get_provider(name, **kwargs):
    """Return a Provider object for the given provider."""
    if name in providers:
        return providers[name](**kwargs)

    raise RuntimeError('Invalid provider "%s"' % name)
    # TODO

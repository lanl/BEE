from beeflow.common.cloud import provider


def test_cloud_api():
    """Simple test to check the cloud provider API."""
    mock = provider.MockProvider()

    mock.setup_cloud('empty config....')

    assert mock.get_ext_ip_addr('some-node')

# TODO: More tests should be added with future API additions

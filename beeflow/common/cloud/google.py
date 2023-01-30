"""Google provider code."""
import time
import googleapiclient.discovery
import yaml

from beeflow.common.cloud import provider


class GoogleProvider(provider.Provider):
    """Google provider class."""

    def __init__(self, project, zone, **kwargs):
        """Google provider constructor."""
        self.params = kwargs
        self.zone = zone
        self.project = project
        # Set defaults here for now
        self._api = googleapiclient.discovery.build('compute', 'v1')

    def get_ext_ip_addr(self, node_name):
        """Get the external IP of this node (or None if no IP)."""
        res = self._api.instances().get(instance=node_name,  # noqa (can't find instances member)
                                        project=self.project,
                                        zone=self.zone).execute()
        try:
            return res['networkInterfaces'][0]['accessConfigs'][0]['natIP']
        except (IndexError, KeyError):
            return None

    def setup_cloud(self, config):
        """Set up the cloud based on the config information."""
        # Load the YAML data
        config = yaml.load(config, Loader=yaml.Loader)
        # This just creates instances one-by-one. There may be a better API call
        # to just create everything at once.
        for instance in config['instances']:
            call = self._api.instances().insert(project=self.project,  # noqa (can't find instances member)
                                                zone=self.zone, body=instance)
            res = call.execute()
            print(res)
            time.sleep(2)

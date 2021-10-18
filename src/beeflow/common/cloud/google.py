"""Google provider code."""
import googleapiclient.discovery
import time
import importlib.util

from beeflow.common.cloud import provider


class TemplateAPI:
    """Template API class to be used by a template."""

    def __init__(self, api, project, zone):
        """Template API class constructor."""
        self.project = project
        self.zone = zone

        self._api = api

    def create_node(self, config):
        """Create a node from a config definition."""
        def create_node(config):
            """Create a node based on a configuration."""
        call = self._api.instances().insert(project=self.project,
                                            zone=self.zone, body=config)
        res = call.execute()


class GoogleProvider(provider.Provider):
    """Google provider class."""

    def __init__(self, project, zone, **kwargs):
        """Google provider constructor."""
        # Set defaults here for now
        self._project = project
        self._zone = zone
        self._kwargs = kwargs
        self._api = googleapiclient.discovery.build('compute', 'v1')

    def create_from_template(self, template_file, **kwargs):
        """Create from a template file."""
        # TODO: Launch from a template file
        spec = importlib.util.spec_from_file_location('bee_template',
                                                      template_file)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        # Call the user template module, passing it a template api object
        template_api = TemplateAPI(self._api, self._project, self._zone)
        mod.setup(template_api=template_api, **self._kwargs)

        # Call the user module, passing it the create_node function
        # mod.setup(create_node=create_node, zone=self._zone, **self._kwargs)

        ## Call the user module, creating a single node template
        #config = mod.create_node_config(zone=self._zone, **self._kwargs)
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

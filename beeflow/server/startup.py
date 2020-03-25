from beeflow.common.config.config_driver import BeeConfig

bc = BeeConfig()

bolt_port = bc.userconfig['graphdb'].get('bolt_port','7687')
http_port = bc.userconfig['graphdb'].get('http_port','7474')
https_port = bc.userconfig['graphdb'].get('https_port','7473')

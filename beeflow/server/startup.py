import sys
import tempfile
from beeflow.common.config.config_driver import BeeConfig

bc = BeeConfig()

if bc.userconfig.has_section('graphdb'):
    graphsec = bc.userconfig['graphdb']
    db_hostname = graphsec.get('hostname','localhost')
    bolt_port = graphsec.get('bolt_port','7687')
    http_port = graphsec.get('http_port','7474')
    https_port = graphsec.get('https_port','7473')
    gdb_img = graphsec.get('gdb_image','')
    gdb_img_mntdir = graphsec.get('gdb_img_mntdir','/tmp')
else:
    print("[graphdb] section not found in configuration file, default values will be added.")

    graphdb_dict = {
        'name': 'graphdb',
        'hostname': 'localhost',
        'bolt_port': 7687,
        'http_port': 7474,
        'https_port': 7473,
        'gdb_img':
        'neo4j-ch.tar',
        'gdb_img_mntdir': '/tmp',
        }

    bc.add_section('user', graphdb_dict)

    sys.exit("Please check " + str(bc.userconfig_file) + " and rerun startup.")


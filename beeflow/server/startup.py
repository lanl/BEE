from beeflow.common.config.config_driver import BeeConfig

bc = BeeConfig()

if bc.userconfig.has_section('graphdb'):
    graphsec = bc.userconfig['graphdb']
    bolt_port = graphsec.get('bolt_port','7687')
    http_port = graphsec.get('http_port','7474')
    https_port = graphsec.get('https_port','7473')
    gdb_img = graphsec.get('gdb_image','')
    gdb_img_mntdir = graphsec.get('gdb_img_mntdir','/tmp')
else:
    print("[graphdb] section not found in user bee.conf.")
    print("Default values will be added to user bee.conf.")
    print("Please edit your bee.conf and rerun startup.")

    graphdb_dict = {
        'name': 'graphdb',
        'bolt_port': 7687,
        'http_port': 7474,
        'https_port': 7473,
        'gdb_img':
        'neo4j-ch.tar',
        'gdb_img_mntdir': '/tmp',
        }

    bc.add_section('user', graphdb_dict)

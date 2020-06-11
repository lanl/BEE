import getpass
import os
import shutil
import subprocess
import sys
import tempfile
from beeflow.common.config.config_driver import BeeConfig

if shutil.which("ch-tar2dir") == None or shutil.which("ch-run") == None:
    sys.exit("ch-tar2dir or ch-run not found. Charliecloud required for execution of startup script.")
    
user_confdir = os.path.expanduser('~/.config/beeflow')
user_conffile = os.path.join(user_confdir, "bee.conf")
if not os.path.exists(user_conffile):
    os.makedirs(user_confdir, exist_ok=True)
    with open(user_conffile, 'w') as conf:
        conf.write("# BEE CONFIGURATION FILE #")
        conf.close()

bc = BeeConfig()

if bc.userconfig.has_section('graphdb'):
    graphsec = bc.userconfig['graphdb']
    db_hostname = graphsec.get('hostname','localhost')
    db_password = graphsec.get('dbpass','password')
    bolt_port = graphsec.get('bolt_port','7687')
    http_port = graphsec.get('http_port','7474')
    https_port = graphsec.get('https_port','7473')
    gdb_img = graphsec.get('gdb_image','')
    gdb_img_mntdir = graphsec.get('gdb_image_mntdir','/tmp')
else:
    print("[graphdb] section not found in configuration file, default values will be added")

    graphdb_dict = {
        'hostname': 'localhost',
        'dbpass': 'password',
        'bolt_port': 7687,
        'http_port': 7474,
        'https_port': 7473,
        'gdb_image': 'neo4j-ch.tar',
        'gdb_image_mntdir': '/tmp',
        }

    bc.add_section('user','graphdb' ,graphdb_dict)

    sys.exit("Please check " + str(bc.userconfig_file) + " and rerun startup")

container_dir = tempfile.mkdtemp(suffix="_" + getpass.getuser(), prefix="gdb_", dir=str(gdb_img_mntdir))
print("GraphDB container mount directory " + container_dir + " created")
newdir = os.path.split(container_dir)[1]

subprocess.run(["ch-tar2dir",str(gdb_img),str(container_dir)])

container_path = container_dir + "/" + os.listdir(str(container_dir))[0]
container_config_path = os.path.join(user_confdir, newdir)
os.mkdir(container_config_path)
gdb_configfile = shutil.copyfile(container_path + "/var/lib/neo4j/conf/neo4j.conf", container_config_path + "/neo4j.conf")
print(gdb_configfile)
if os.path.exists(container_path + "/var/lib/neo4j/data/dbms/auth"):
    os.remove(container_path + "/var/lib/neo4j/data/dbms/auth")

cfile = open(gdb_configfile, "rt")
data = cfile.read()
cfile.close()
data = data.replace("#dbms.connector.bolt.listen_address=:7687", "dbms.connector.bolt.listen_address=:" + str(bolt_port))
data = data.replace("#dbms.connector.http.listen_address=:7474", "dbms.connector.http.listen_address=:" + str(http_port))
data = data.replace("#dbms.connector.https.listen_address=:7473", "dbms.connector.https.listen_address=:" + str(https_port))
cfile = open(gdb_configfile, "wt")
cfile.write(data)
cfile.close()

subprocess.run(["ch-run","-w","--set-env=" + container_path + "/environment","-b",container_config_path + ":/var/lib/neo4j/conf",container_path,"--","neo4j-admin","set-initial-password",str(db_password)])

subprocess.run(["ch-run","-w","--set-env=" + container_path + "/environment","-b",container_config_path + ":/var/lib/neo4j/conf",container_path,"--","neo4j","console"])

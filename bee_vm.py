import subprocess
from qmp import QEMUMonitorProtocol
from host import Host
from qemu import QEMU
from docker import Docker
import os

class BeeVM(object):
    def __init__(self, hostname, host, rank, job_conf, bee_vm_conf, 
                 key_path, base_img, img, network_mode, storage_mode):
        
        # Basic configurations
        self.status = ""
        self.hostname = hostname
        self.__rank = rank
        self.master = ""
        self.__user_name = "ubuntu"
        self.__key_path = key_path

        # Images
        self.base_img = base_img
        self.img = img
        self.base_data_img = ""
        self.data_img = ""

        # Hardware configurations
        self.ram_size = bee_vm_conf['ram_size']
        self.cpu_cores = bee_vm_conf['cpu_core_per_socket']
        self.cpu_threads = bee_vm_conf['cpu_thread_per_core']
        self.cpu_sockets = bee_vm_conf['cpu_sockets']
        
        # Network configurations
        # 1st vNIC
        self.ssh_port = 5555
        # 2nd vNIC
        self.subnet = 7 #to be replaced
        self.mac_adder = "02:00:00:00:{0:02x}:{1:02x}".format(self.subnet, rank + 1)
        self.__IP = "192.168.{}.{}".format(self.subnet, rank + 1)
        # Multicast mode
        self.mcast_port = 1234
        # P2P sockets mode
        self.listen_port_base = 10000
        self.port_base_offset = 0
        self.listen_port = []
        self.connect_host = []
        self.connect_port = []
        
        # Storage configurations
        self.mount_tag = "hostshare"
        self.host_shared_dir = bee_vm_conf['host_input_dir']
        self.vm_shared_dir = "/home/ubuntu/vmshare"
        
        # Network & Storage mode flags
        self.network_mode = network_mode
        self.storage_mode = storage_mode

        # Docker container
        self.__docker = ""

        # Run command on this VM
        # none root
        self.__exec_cmd = ["ssh",
                           "-p {}".format(self.ssh_port),
                           "-o StrictHostKeyChecking=no",
                           "-o ConnectTimeout=300",
                           "-o UserKnownHostsFile=/dev/null",
                           "-q",
                           "-i {}".format(self.__key_path),
                           "{}@localhost".format(self.__user_name),
                           "-x"]
        # root
        self.__root_exec_cmd = ["ssh", 
                                "-p {}".format(self.ssh_port),
                                "-o StrictHostKeyChecking=no",
                                "-o ConnectTimeout=300",
                                "-o UserKnownHostsFile=/dev/null",
                                "-q",
                                "-i {}".format(self.__key_path),
                                "{}@localhost".format('root'),
                                "-x"]

        # Host machine
        self.__host = Host(host)

        # QEMU
        self.__kvm = True
        self.__hypervisor = QEMU(host, "qemu-system-x86_64", self.__kvm)

        # Job Configuration
        self.__job_conf = job_conf
    
    def get_ip(self):
        return self.__IP

    def get_hostname(self):
        return self.hostname
    
    def set_hostname(self):
        cmd = ["hostname",
               self.hostname]
        self.root_run(cmd)

    def add_host_list(self, private_ip, hostname):
        cmd = ["echo",
               "\"{} {}\"".format(private_ip, hostname),
               "|",
               "tee --append",
               " /etc/hosts"]
        self.root_run(cmd)


    def set_master(self, master):
        self.master = master

    def get_listen_port(self):
        new_port = self.listen_port_base + self.port_base_offset
        self.port_base_offset = self.port_base_offset + 1
        return new_port

    def connect_to_me(self, vm):
        new_listen_port = self.get_listen_port()
        self.listen_port.append(new_listen_port)
        vm.connect_host.append(self.__host)
        vm.connect_port.append(new_listen_port)

    def run(self, command):
        # Execute command on this VM.
        cmd = self.__exec_cmd + ["'"] + command + ["'"]
        self.__host.run(cmd)
        
    def root_run(self, command):
        # Execute command with root previlege on this VM.
        cmd = self.__root_exec_cmd + ["'"] + command + ["'"]
        self.__host.run(cmd)

    def parallel_run(self, command, vms):
        cmd = ["mpirun",
               "--mca btl_tcp_if_include eth0",
               "-host"]
        vm_list = ""
        for vm in vms:
            vm_name = vm.get_hostname()
            vm_list = vm_list + vm_name + ","
        cmd.append(vm_list)
        cmd = cmd + command        
        self.run(cmd)

    def set_data_img(self, base_data_img, data_img):
        self.base_data_img = base_data_img
        self.data_img = data_img

    def create_shared_dir(self):
        # Create directory
        cmd = ["mkdir",
               "{}".format(self.vm_shared_dir)]
        self.root_run(cmd)

    def update_ownership(self):
        cmd = ["chown",
               "-R",
               "{}:{}".format(self.__user_name,self.__user_name),
               "{}".format(self.vm_shared_dir)]
        self.root_run(cmd)

    # Storage mode 3
    def mount_virtio(self):
        # Mount host's shared dir to VM.
        cmd = ["mount",
               "-t 9p",
               "-o trans=virtio,version=9p2000.L",
               "{}".format(self.mount_tag),
               "{}".format(self.vm_shared_dir)]
        self.root_run(cmd)

    # Storage mode 1
    def set_data_img(self, base_data_img, data_img):
        self.base_data_img = base_data_img
        self.data_img = data_img

    def mount_data_img(self):
        # Mount data image.
        cmd = ["mount",
               "/dev/sdb",
               "{}".format(self.vm_shared_dir)]
        self.root_run(cmd)

    def mount_nfs(self, url):
        # Mount nfs directory
        cmd = ["mount",
               "{}".format(url),
               "{}".format(self.vm_shared_dir)]
        self.root_run(cmd)

    def mount_master_data_img(self):
        url = "{}:{}".format(self.master.get_hostname(), self.vm_shared_dir)
        self.mount_nfs(url)

    def update_uid(self): 
        # Change user's UID to match host's UID.
        # This is necessary for dir sharing.
        cmd = ["usermod",
               "-u {} {}".format(os.getuid(), self.__user_name)]
        
        self.root_run(cmd)

    def update_gid(self):
        # Change user's GID to match host's GID.
        # This is necessary for dir sharing. 
        cmd = ["groupmod",
               "-g {} {}".format(os.getgid(), self.__user_name)]
        
        self.root_run(cmd)

    def copy_file(self, src_path, dist_path):
        cmd = ["scp",
               "-P {}".format(self.ssh_port),
               "-i {}".format(self.__key_path),
               "{}".format(src_path),
               "{}@localhost:{}".format(self.__user_name, dist_path)]
        self.__host.run(cmd)

    def create_os_img(self):
        self.__host.run(self.__hypervisor.create_img(self.base_img, self.img))

    def create_data_img(self):
        self.__host.run(self.__hypervisor.create_img(self.base_data_img, self.data_img))

    def start(self):
        self.__host.run(self.__hypervisor.start_vm(self))
    
    def kill(self):
        self.__host.kill_all_vms()
    


    # Following are functions for the Docker container.
    def add_docker_container(self, docker):
        self.__docker = docker

    def get_dockerfile(self, vms):
        self.parallel_run(self.__docker.get_dockerfile(), vms)   
        
    def get_docker_img(self, vms):
        self.parallel_run(self.__docker.get_docker_img(), vms)

    def build_docker(self, vms):
        self.parallel_run(self.__docker.build_docker(), vms)      

    def start_docker(self, exec_cmd):
        self.run(self.__docker.start_docker(exec_cmd)) 
        
    def docker_update_uid(self):
        self.run(self.__docker.update_uid(os.getuid()))

    def docker_update_gid(self):
        self.run(self.__docker.update_gid(os.getgid()))
        
    def docker_copy_file(self, src_path, dist_path):
        self.run(self.__docker.copy_file(src_path, dist_path))

    def docker_seq_run(self, exec_cmd):
        self.run(self.__docker.run([exec_cmd]))

    def docker_para_run(self, exec_cmd, vms):
        np = int(self.__job_conf['proc_per_node']) * int(self.__job_conf['num_of_nodes'])
        cmd = ["mpirun",
               "--allow-run-as-root",
               "--mca btl_tcp_if_include eth0",
               "--hostfile /root/hostfile",
               "-np {}".format(np)]
        cmd = cmd + [exec_cmd]
        self.run(self.__docker.run(cmd))

    def docker_make_hostfile(self, vms, tmp_dir):
        hostfile_path = "{}/hostfile".format(tmp_dir)
        cmd = ["rm",
               hostfile_path]
        self.__host.run(cmd)

        cmd = ["touch",
               hostfile_path]
        self.__host.run(cmd)
        
        for vm in vms:
            cmd = ["echo",
                   "\"{} slots={} \"".format(vm.get_hostname(), self.__job_conf['proc_per_node']),
                   "|",
                   "tee --append",
                   hostfile_path]
            self.__host.run(cmd)

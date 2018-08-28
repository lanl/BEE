import subprocess
from qmp import QEMUMonitorProtocol
from host import Host
from qemu import QEMU
from docker import Docker
import os
from termcolor import colored, cprint
import pexpect,sys

class BeeVM(object):
    def __init__(self, task_id, hostname, host, rank, task_conf, bee_vm_conf, 
                 key_path, base_img, img, network_mode, storage_mode):
        
        #qemu process
        self.__pexpect_child = ""
        
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
        self.subnet = task_id + 9 # Different group has different subnet
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

        # root
        self.__root_exec_cmd = ["ssh", 
                                "-p {}".format(self.ssh_port),
                                "-o StrictHostKeyChecking=no",
                                "-o ConnectTimeout=300",
                                "-o UserKnownHostsFile=/dev/null",
                                "-i {}".format(self.__key_path),
                                "{}@localhost".format('root'),
                                "-x"]

        # Host machine
        self.__host = Host(host)

        # QEMU
        self.__kvm = True
        self.__hypervisor = QEMU(host, "qemu-system-x86_64", self.__kvm)

        # Job Configuration
        self.__task_conf = task_conf
        
        # Output color list
        self.__output_color_list = ["magenta", "cyan", "blue", "green", "red", "grey", "yellow"]
        #self.__output_color = self.__output_color_list[task_id % 7]
        self.__output_color = "cyan"

    def get_ip(self):
        return self.__IP

    def get_hostname(self):
        return self.hostname
    
    def set_hostname(self):
        cprint("["+self.hostname+"]: set hostname.", self.__output_color)
        cmd = ["hostname",
               self.hostname]
        self.root_run(cmd)

    def add_host_list(self, private_ip, hostname):
        cprint("["+self.hostname+"]: set hosts file for MPI.", self.__output_color)
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

    def run(self, command, local_pfwd = [], remote_pfwd = [], async = False):
        # Execute command on this VM.
        exec_cmd = ["ssh",
                    "-p {}".format(self.ssh_port),
                    "-o StrictHostKeyChecking=no",
                    "-o ConnectTimeout=300",
                    "-o UserKnownHostsFile=/dev/null",
                    "-i {}".format(self.__key_path),
                    "{}@localhost".format(self.__user_name),
                    "-x"]
        for port in local_pfwd:
            exec_cmd.insert(7, "-L {}:localhost:{}".format(port, port))
        for port in remote_pfwd:
            exec_cmd.insert(7, "-R {}:localhost:{}".format(port, port))

        cmd = exec_cmd + ["'"] + command + ["'"]

        return self.__host.run(cmd, local_pfwd = local_pfwd, remote_pfwd = remote_pfwd, async = async)



    def root_run(self, command, local_pfwd = [], remote_pfwd = [], async = False):
        # Execute command with root previlege on this VM.
        root_exec_cmd = ["ssh",
                         "-p {}".format(self.ssh_port),
                         "-o StrictHostKeyChecking=no",
                         "-o ConnectTimeout=300",
                         "-o UserKnownHostsFile=/dev/null",
                         "-i {}".format(self.__key_path),
                         "{}@localhost".format('root'),
                         "-x"]
        for port in local_pfwd:
            exec_cmd.insert(7, "-L {}:localhost:{}".format(port, port))
        for port in remote_pfwd:
            exec_cmd.insert(7, "-R {}:localhost:{}".format(port, port))

        cmd = root_exec_cmd + ["'"] + command + ["'"]
        return self.__host.run(cmd, local_pfwd = local_pfwd, remote_pfwd = remote_pfwd, async = async)

    def parallel_run(self, command, vms, local_pfwd = [], remote_pfwd = [], async = False):
        cmd = ["mpirun",
               "--mca btl_tcp_if_include eth0",
               "-host"]
        vm_list = ""
        for vm in vms:
            vm_name = vm.get_hostname()
            vm_list = vm_list + vm_name + ","
        cmd.append(vm_list)
        cmd = cmd + command        
        return self.run(cmd, local_pfwd = local_pfwd, remote_pfwd = remote_pfwd, async = async)

    def set_data_img(self, base_data_img, data_img):
        self.base_data_img = base_data_img
        self.data_img = data_img

    def create_shared_dir(self):
        # Create directory
        cprint("["+self.hostname+"]: create shared directory.", self.__output_color)
        cmd = ["mkdir",
               "{}".format(self.vm_shared_dir)]
        self.root_run(cmd)

    def update_ownership(self):
        cprint("["+self.hostname+"]: update ownership of shared directory.", self.__output_color)
        cmd = ["chown",
               "-R",
               "{}:{}".format(self.__user_name,self.__user_name),
               "{}".format(self.vm_shared_dir)]
        self.root_run(cmd)

    # Storage mode 3
    def mount_virtio(self):
        cprint("["+self.hostname+"]: mount shared directory (via 9p).", self.__output_color)
        # Mount host's shared dir to VM.
        ''' 
	cmd = ["mount",
               "-t 9p",
               "-o trans=virtio,version=9p2000.L",
               "{}".format(self.mount_tag),
               "{}".format(self.vm_shared_dir)]
        '''
	cmd = ["mount", "-t 9p", "-o trans=virtio,msize=262144", "{}".format(self.mount_tag), "{}".format(self.vm_shared_dir), "-oversion=9p2000.L"]
	# cmd = ["mount", "-t 9p", "-o trans=virtio,msize=524288,version=9p2000.L", "{}".format(self.mount_tag), "{}".format(self.vm_shared_dir)]
	self.root_run(cmd)

    # Storage mode 1
    def set_data_img(self, base_data_img, data_img):
        self.base_data_img = base_data_img
        self.data_img = data_img

    def mount_data_img(self):
        cprint("["+self.hostname+"]: mount data image.", self.__output_color)
        # Mount data image.
        cmd = ["mount",
               "/dev/sdb",
               "{}".format(self.vm_shared_dir)]
        self.root_run(cmd)

    def mount_nfs(self, url):
        cprint("["+self.hostname+"]: mount nfs.", self.__output_color)
        # Mount nfs directory
        cmd = ["mount",
               "{}".format(url),
               "{}".format(self.vm_shared_dir)]
        self.root_run(cmd)

    def mount_master_data_img(self):
        cprint("["+self.hostname+"]: mount master data image.", self.__output_color)
        url = "{}:{}".format(self.master.get_hostname(), self.vm_shared_dir)
        self.mount_nfs(url)

    def update_uid(self): 
        cprint("["+self.hostname+"]: update user UID.", self.__output_color)
        # Change user's UID to match host's UID.
        # This is necessary for dir sharing.
        cmd = ["usermod",
               "-u {} {}".format(os.getuid(), self.__user_name)]
        
        self.root_run(cmd)

    def update_gid(self):
        cprint("["+self.hostname+"]: update user GID.", self.__output_color)
        # Change user's GID to match host's GID.
        # This is necessary for dir sharing. 
        cmd = ["groupmod",
               "-g {} {}".format(os.getgid(), self.__user_name)]
        
        self.root_run(cmd)

    def update_mtu(self):
	cprint("["+self.hostname+"]: change eth0 mtu.", self.__output_color)
	# Change MTU for eth0 in vm
	# Necessary for good network performance
	cmd = ["ifconfig", "eth0", "mtu", "15000"]
	self.root_run(cmd)

    def copy_file(self, src_path, dist_path):
        cprint("["+self.hostname+"]: copy file:"+src_path+" --> "+dist_path+".", self.__output_color)
        cmd = ["scp",
               "-P {}".format(self.ssh_port),
               "-i {}".format(self.__key_path),
               "-o StrictHostKeyChecking=no",
               "-o ConnectTimeout=300",
               "-o UserKnownHostsFile=/dev/null",
               "{}".format(src_path),
               "{}@localhost:{}".format(self.__user_name, dist_path)]
        self.__host.run(cmd)

    def create_os_img(self):
        cprint("["+self.hostname+"]: create new OS image.", self.__output_color)
        self.__host.run(self.__hypervisor.create_img(self.base_img, self.img))

    def create_data_img(self):
        cprint("["+self.hostname+"]: create new data image.", self.__output_color)
        self.__host.run(self.__hypervisor.create_img(self.base_data_img, self.data_img))

    def start(self):
        cprint("["+self.hostname+"]: starting BEE-VM.", self.__output_color)
        cmd = self.__host.compose_cmd(self.__hypervisor.start_vm(self))
        cmd = " ".join(cmd)
        print(cmd)
        self.__pexpect_child = pexpect.spawn(cmd)
        self.__pexpect_child.logfile = sys.stdout 
        
        # do nothing just used for starting the process
        self.__pexpect_child.expect('(qemu)')
        self.__pexpect_child.sendline('info snapshots')

    def checkpoint(self):
        cprint("["+self.hostname+"]: checkpointing BEE-VM.", self.__output_color)
        self.__pexpect_child.expect('(qemu)')
        self.__pexpect_child.sendline('savevm bee_saved')
        cprint("["+self.hostname+"]: checkpointing BEE-VM complete.", self.__output_color)

    def restore(self):
        cprint("["+self.hostname+"]: restoringing BEE-VM.", self.__output_color)
        self.__pexpect_child.expect('(qemu)')
        self.__pexpect_child.sendline('loadvm bee_saved')
        cprint("["+self.hostname+"]: restoringing BEE-VM complete.", self.__output_color)
    

    def kill(self):
        cprint("["+self.hostname+"]: killing BEE-VM.", self.__output_color)
        self.__host.kill_all_vms()
    


    # Following are functions for the Docker container.
    def add_docker_container(self, docker):
        self.__docker = docker

    def get_dockerfile(self, vms):
        self.parallel_run(self.__docker.get_dockerfile(), vms)   
        
    def get_docker_img(self, vms):
        cprint("["+self.hostname+"]: pull docker image in parallel.", self.__output_color)
        self.parallel_run(self.__docker.get_docker_img(), vms)

    def build_docker(self, vms):
        self.parallel_run(self.__docker.build_docker(), vms)      

    def start_docker(self, exec_cmd):
        cprint("["+self.hostname+"]: start docker container.", self.__output_color)
        self.run(self.__docker.start_docker(exec_cmd)) 
        
    def docker_update_uid(self):
        cprint("["+self.hostname+"][Docker]: update docker user UID.", self.__output_color)
        self.run(self.__docker.update_uid(os.getuid()))

    def docker_update_gid(self):
        cprint("["+self.hostname+"][Docker]: update docker user GID.", self.__output_color)
        self.run(self.__docker.update_gid(os.getgid()))
        
    def docker_copy_file(self, src, dest):
        cprint("["+self.hostname+"][Docker]: copy file to docker" + src + " --> " + dest +".", self.__output_color)
        self.run(self.__docker.copy_file(src, dest))
        self.run(self.__docker.update_file_ownership(dest))

    def docker_seq_run(self, exec_cmd, local_pfwd = [], remote_pfwd = [], async = False):
        cprint("["+self.hostname+"][Docker]: run script:"+exec_cmd+".", self.__output_color)
        return self.run(self.__docker.run([exec_cmd]), local_pfwd = local_pfwd, remote_pfwd = remote_pfwd, async = async)

    def docker_para_run(self, run_conf, exec_cmd, hostfile_path, local_pfwd = [], remote_pfwd = [], async = False):
        cprint("["+self.hostname+"][Docker]: run parallel script:" + exec_cmd + ".", self.__output_color)
        np = int(run_conf['proc_per_node']) * int(run_conf['num_of_nodes'])
        cmd = ["mpirun",
               "--allow-run-as-root",
               "--mca btl_tcp_if_include eth0",
               "--hostfile {}".format(hostfile_path),
               "-np {}".format(np)]
        cmd = cmd + [exec_cmd]
        return self.run(self.__docker.run(cmd), local_pfwd = local_pfwd, remote_pfwd = remote_pfwd, async = async)

    def docker_make_hostfile(self, run_conf, vms, tmp_dir):
        cprint("["+self.hostname+"][Docker]: prepare hostfile.", self.__output_color)
        hostfile_path = "{}/hostfile".format(tmp_dir)
        # Remove old hostfile
        cmd = ["rm",hostfile_path]
        self.__host.run(cmd)
        # Create new hostfile
        cmd = ["touch", hostfile_path]
        self.__host.run(cmd)
        # Add nodes to hostfile
        for vm in vms:
            cmd = ["echo",
                   "\"{} slots={} \"".format(vm.get_hostname(), run_conf['proc_per_node']),
                   "|",
                   "tee --append",
                   hostfile_path]
            self.__host.run(cmd)

# system
import os
import subprocess
from termcolor import cprint
# project
from host import Host


class BeeNode(object):
    def __init__(self, task_id, hostname, host, rank, task_conf):
        # Basic configurations
        self.__status = ""
        self.__hostname = hostname
        self.__rank = rank
        self.__master = ""

        # Job configuration
        self.__task_id = task_id
        self.__task_conf = task_conf

        # Host machine
        self.__host = Host(host)

        # Output color list
        self.__output_color_list = ["magenta", "cyan", "blue", "green",
                                    "red", "grey", "yellow"]
        self.__output_color = "cyan"
        self.__error_color = "red"

    # Accessors
    def get_hostname(self):
        return self.__hostname

    def get_status(self):
        return self.__status

    def get_master(self):
        return self.__master

    # Modifiers
    def set_hostname(self):
        cprint("[" + self.__hostname + "]: set hostname.", self.__output_color)
        cmd = ["hostname",
               self.__hostname]
        self.root_run(cmd)

    def set_status(self, status):
        cprint("[" + self.__hostname + "]Setting status", self.__output_color)
        self.__status = status

    def set_master(self, master):
        self.__master = master

    def run(self, command, local_pfwd=None, remote_pfwd=None, async=False):
        return self.__host.run(command=command, local_pfwd=local_pfwd,
                               remote_pfwd=remote_pfwd, async=async)

    def root_run(self, command, local_pfwd=None, remote_pfwd=None, async=False):
        pass

    def parallel_run(self, command, vms, local_pfwd=None, remote_pfwd=None, async=False):
        cmd = ["mpirun",
               "--mca btl_tcp_if_include eth0",
               "-host"]
        vm_list = ""
        for vm in vms:
            vm_name = vm.get_hostname()
            vm_list = vm_list + vm_name + ","
        cmd.append(vm_list)
        cmd = cmd + command
        return self.run(cmd, local_pfwd=local_pfwd, remote_pfwd=remote_pfwd, async=async)

    def set_data_img(self, base_data_img, data_img):
        self.base_data_img = base_data_img
        self.data_img = data_img

    def create_shared_dir(self):
        # Create directory
        cprint("[" + self.hostname + "]: create shared directory.", self.__output_color)
        cmd = ["mkdir",
               "{}".format(self.vm_shared_dir)]
        self.root_run(cmd)

    def update_ownership(self):
        cprint("[" + self.hostname + "]: update ownership of shared directory.", self.__output_color)
        cmd = ["chown",
               "-R",
               "{}:{}".format(self.__user_name, self.__user_name),
               "{}".format(self.vm_shared_dir)]
        self.root_run(cmd)

    # Storage mode 3
    def mount_virtio(self):
        cprint("[" + self.hostname + "]: mount shared directory (via 9p).", self.__output_color)
        # Mount host's shared dir to VM.
        ''' 
	cmd = ["mount",
               "-t 9p",
               "-o trans=virtio,version=9p2000.L",
               "{}".format(self.mount_tag),
               "{}".format(self.vm_shared_dir)]
        '''
        cmd = ["mount", "-t 9p", "-o trans=virtio,msize=262144", "{}".format(self.mount_tag),
               "{}".format(self.vm_shared_dir), "-oversion=9p2000.L"]
        # cmd = ["mount", "-t 9p", "-o trans=virtio,msize=524288,version=9p2000.L", "{}".format(self.mount_tag), "{}".format(self.vm_shared_dir)]
        self.root_run(cmd)

    # Storage mode 1
    def set_data_img(self, base_data_img, data_img):
        self.base_data_img = base_data_img
        self.data_img = data_img

    def mount_data_img(self):
        cprint("[" + self.hostname + "]: mount data image.", self.__output_color)
        # Mount data image.
        cmd = ["mount",
               "/dev/sdb",
               "{}".format(self.vm_shared_dir)]
        self.root_run(cmd)

    def mount_nfs(self, url):
        cprint("[" + self.hostname + "]: mount nfs.", self.__output_color)
        # Mount nfs directory
        cmd = ["mount",
               "{}".format(url),
               "{}".format(self.vm_shared_dir)]
        self.root_run(cmd)

    def mount_master_data_img(self):
        cprint("[" + self.hostname + "]: mount master data image.", self.__output_color)
        url = "{}:{}".format(self.master.get_hostname(), self.vm_shared_dir)
        self.mount_nfs(url)

    def update_uid(self):
        cprint("[" + self.hostname + "]: update user UID.", self.__output_color)
        # Change user's UID to match host's UID.
        # This is necessary for dir sharing.
        cmd = ["usermod",
               "-u {} {}".format(os.getuid(), self.__user_name)]

        self.root_run(cmd)

    def update_gid(self):
        cprint("[" + self.hostname + "]: update user GID.", self.__output_color)
        # Change user's GID to match host's GID.
        # This is necessary for dir sharing.
        cmd = ["groupmod",
               "-g {} {}".format(os.getgid(), self.__user_name)]

        self.root_run(cmd)

    def update_mtu(self):
        cprint("[" + self.hostname + "]: change eth0 mtu.", self.__output_color)
        # Change MTU for eth0 in vm
        # Necessary for good network performance
        cmd = ["ifconfig", "eth0", "mtu", "15000"]
        self.root_run(cmd)

    def copy_file(self, src_path, dist_path):
        cprint("[" + self.hostname + "]: copy file:" + src_path + " --> " + dist_path + ".", self.__output_color)
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
        cprint("[" + self.hostname + "]: create new OS image.", self.__output_color)
        self.__host.run(self.__hypervisor.create_img(self.base_img, self.img))

    def create_data_img(self):
        cprint("[" + self.hostname + "]: create new data image.", self.__output_color)
        self.__host.run(self.__hypervisor.create_img(self.base_data_img, self.data_img))

    def start(self):
        cprint("[" + self.hostname + "]: starting BEE-VM.", self.__output_color)
        cmd = self.__host.compose_cmd(self.__hypervisor.start_vm(self))
        cmd = " ".join(cmd)
        print(cmd)
        self.__pexpect_child = pexpect.spawn(cmd)
        self.__pexpect_child.logfile = sys.stdout

        # do nothing just used for starting the process
        self.__pexpect_child.expect('(qemu)')
        self.__pexpect_child.sendline('info snapshots')

    def checkpoint(self):
        cprint("[" + self.hostname + "]: checkpointing BEE-VM.", self.__output_color)
        self.__pexpect_child.expect('(qemu)')
        self.__pexpect_child.sendline('savevm bee_saved')
        cprint("[" + self.hostname + "]: checkpointing BEE-VM complete.", self.__output_color)

    def restore(self):
        cprint("[" + self.hostname + "]: restoringing BEE-VM.", self.__output_color)
        self.__pexpect_child.expect('(qemu)')
        self.__pexpect_child.sendline('loadvm bee_saved')
        cprint("[" + self.hostname + "]: restoringing BEE-VM complete.", self.__output_color)

    def kill(self):
        cprint("[" + self.hostname + "]: killing BEE-VM.", self.__output_color)
        self.__host.kill_all_vms()

    # Following are functions for the Docker container.
    def add_docker_container(self, docker):
        self.__docker = docker

    def get_dockerfile(self, vms):
        self.parallel_run(self.__docker.get_dockerfile(), vms)

    def get_docker_img(self, vms):
        cprint("[" + self.hostname + "]: pull docker image in parallel.", self.__output_color)
        self.parallel_run(self.__docker.get_docker_img(), vms)

    def build_docker(self, vms):
        self.parallel_run(self.__docker.build_docker(), vms)

    def start_docker(self, exec_cmd):
        cprint("[" + self.hostname + "]: start docker container.", self.__output_color)
        self.run(self.__docker.start_docker(exec_cmd))

    def docker_update_uid(self):
        cprint("[" + self.hostname + "][Docker]: update docker user UID.", self.__output_color)
        self.run(self.__docker.update_uid(os.getuid()))

    def docker_update_gid(self):
        cprint("[" + self.hostname + "][Docker]: update docker user GID.", self.__output_color)
        self.run(self.__docker.update_gid(os.getgid()))

    def docker_copy_file(self, src, dest):
        cprint("[" + self.hostname + "][Docker]: copy file to docker" + src + " --> " + dest + ".", self.__output_color)
        self.run(self.__docker.copy_file(src, dest))
        self.run(self.__docker.update_file_ownership(dest))

    def docker_seq_run(self, exec_cmd, local_pfwd=[], remote_pfwd=[], async=False):
        cprint("[" + self.hostname + "][Docker]: run script:" + exec_cmd + ".", self.__output_color)
        return self.run(self.__docker.run([exec_cmd]), local_pfwd=local_pfwd, remote_pfwd=remote_pfwd, async=async)

    def docker_para_run(self, run_conf, exec_cmd, hostfile_path, local_pfwd=[], remote_pfwd=[], async=False):
        cprint("[" + self.hostname + "][Docker]: run parallel script:" + exec_cmd + ".", self.__output_color)
        np = int(run_conf['proc_per_node']) * int(run_conf['num_of_nodes'])
        cmd = ["mpirun",
               "--allow-run-as-root",
               "--mca btl_tcp_if_include eth0",
               "--hostfile {}".format(hostfile_path),
               "-np {}".format(np)]
        cmd = cmd + [exec_cmd]
        return self.run(self.__docker.run(cmd), local_pfwd=local_pfwd, remote_pfwd=remote_pfwd, async=async)

    def docker_make_hostfile(self, run_conf, vms, tmp_dir):
        cprint("[" + self.hostname + "][Docker]: prepare hostfile.", self.__output_color)
        hostfile_path = "{}/hostfile".format(tmp_dir)
        # Remove old hostfile
        cmd = ["rm", hostfile_path]
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

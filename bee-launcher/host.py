import time
import subprocess
from subprocess import Popen
import os
from qemu import QEMU

class Host(object):
    def __init__(self, host_name, ssh_port = 22):
        self.__user_name = os.getlogin()
        self.__uid = os.getuid()
        self.__gid = os.getgid()
        self.__host_name = host_name
        self.__ssh_port = ssh_port
        self.__kvm = True

        self.__vm = ""
        self.__vm_monitor = ""
        self.__hypervisor = QEMU(host_name, "qemu-system-x86_64", self.__kvm)
        

    def get_name(self):
        return self.__host_name

    def run(self, command):        
        exec_cmd = ["ssh",
                    "-p {}".format(self.__ssh_port),
                    "-o StrictHostKeyChecking=no",
                    "-o UserKnownHostsFile=/dev/null",
                    "-q",
                    "{}@{}".format(self.__user_name, self.__host_name),
                    "-x"]
        
        cmd = exec_cmd + command
        #print(" ".join(cmd))
        subprocess.call(cmd)

    def run_pfwd(self, command, port):
        exec_cmd = ["ssh",
                    "-p {}".format(self.__ssh_port),
                    "-o StrictHostKeyChecking=no",
                    "-o UserKnownHostsFile=/dev/null",
                    "-q",
                    "-L {}:localhost:{}".format(port, port),
                    "{}@{}".format(self.__user_name, self.__host_name),
                    "-x"]
        cmd = exec_cmd + command
        #print(" ".join(cmd))  
        subprocess.call(cmd)

    def run_async(self, command):
        exec_cmd = ["ssh",
                    "-p {}".format(self.__ssh_port),
                    "-o StrictHostKeyChecking=no",
                    "-o UserKnownHostsFile=/dev/null",
                    "-q",
                    "{}@{}".format(self.__user_name, self.__host_name),
                    "-x"]

        cmd = exec_cmd + command
        #print(" ".join(cmd))
        Popen(cmd)

    def run_pfwd_async(self, command, port):
        exec_cmd = ["ssh",
                    "-p {}".format(self.__ssh_port),
                    "-o StrictHostKeyChecking=no",
                    "-o UserKnownHostsFile=/dev/null",
                    "-q",
                    "-L {}:localhost:{}".format(port, port),
                    "{}@{}".format(self.__user_name, self.__host_name),
                    "-x"]
        cmd = exec_cmd + command
        #print(" ".join(cmd))
        Popen(cmd)
    # Following are warpper functions of vms

    def add_vm(self, vm):
        self.__vm = vm

    def add_hypervisor(self, hypervisor):
        self.__hypervisor = hypervisor

    def qemu_create_vm_img(self):
        print("create os img for vm[" + self.__vm.get_hostname() + "]")
        self.run(self.__hypervisor.create_img(self.__vm.base_img, self.__vm.img))

    def qemu_create_vm_data_img(self):
        print("create data img for vm[" + self.__vm.get_hostname() + "]")
        self.run(self.__hypervisor.create_img(self.__vm.base_data_img, self.__vm.data_img))
        
    def qemu_start_vm(self):
        print("create vm[" +  self.__vm.get_hostname() + "] on" + self.__host_name)
        self.run(self.__hypervisor.start_vm(self.__vm))
        if not self.__kvm:
            time.sleep(360)

#    def vm_create_shared_dir(self):
#        print("vm[" + self.__vm.get_hostname() + "]:create shared dir")
#        self.run(self.__vm.create_shared_dir())
#
#    def vm_update_ownership(self):
#        print("vm[" + self.__vm.get_hostname() + "]:change ownership of shared dir")
#        self.run(self.__vm.update_ownership())
#
#    def vm_mount_virtio(self):
#        print("vm[" + self.__vm.get_hostname() + "]:mount virtio")
#        self.run(self.__vm.mount_virtio())

#    def vm_set_data_img(self, base_data_img, data_img):
#        print("vm[" + self.__vm.get_hostname() + "]:add data img")
#        self.__vm.set_data_img(base_data_img, data_img)

#    def vm_mount_data_img(self):
#        print("vm[" + self.__vm.get_hostname() + "]:mount data img")
#        self.run(self.__vm.mount_data_img())

#    def vm_mount_master_data_img(self):
#        print("vm[" + self.__vm.get_hostname() + "]:mount master shared dir")
#        self.run(self.__vm.mount_master_data_img())

#    def vm_mount_nfs(self, url):
#        print("vm[" + self.__vm.get_hostname() + "]:mount shared dir")
#        self.run(self.__vm.mount_nfs(url))

#    def vm_update_uid(self):
#        print("vm[" + self.__vm.get_hostname() + "]:update uid = " + str(self.__uid))
#        self.run(self.__vm.update_uid(self.__uid))

#    def vm_update_gid(self):
#        print("vm[" +  self.__vm.get_hostname() + "]:update gid = " + str(self.__gid))
#        self.run(self.__vm.update_gid(self.__gid))

#    def vm_add_docker_container(self, docker):
#        print("vm[" +  self.__vm.get_hostname() + "]:add Docker")
#        self.__vm.add_docker_container(docker)

#    def vm_set_vol_mapping(self, docker_shared_dir):
#        print("vm[" +  self.__vm.get_hostname() + "]:set Docker vol mapping")
#        self.__vm.set_vol_mapping(docker_shared_dir)
        
#    def vm_get_dockerfile(self, vms):
#        self.run(self.__vm.get_dockerfile( vms))

#    def vm_get_docker_img(self, vms):
#        print("vm[" + self.__vm.get_hostname() + "]:get Docker img")
#        self.run(self.__vm.get_docker_img(vms))

#    def vm_build_docker(self, vms):
#        self.run(self.__vm.build_docker(vms))

#    def vm_start_docker(self, exec_cmd):
#        print("vm[" + self.__vm.get_hostname() + "]:start Docker")
#        self.run(self.__vm.start_docker(exec_cmd))

#    def docker_update_uid(self):
#        print("Docker[" + self.__vm.get_hostname() + "]:update uid = " + str(self.__uid))
#        self.run(self.__vm.docker_update_uid(self.__uid))

#    def docker_update_gid(self):
#        print("Docker[" + self.__vm.get_hostname() + "]:update gid = " + str(self.__gid))
#        self.run(self.__vm.docker_update_gid(self.__gid))

    def kill_all_vms(self):
        print("Host[" + self.__host_name + "]:killing all vms")
        cmd = ["pkill",
               "-u {}".format(self.__user_name),
               "qemu-system-x86"]
        self.run(cmd)

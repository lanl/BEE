from hypervisor import Hypervisor
import subprocess
from qmp import QEMUMonitorProtocol
import time

class QEMU(Hypervisor):
    def __init__(self, host_name, qemu_exec, kvm_enabled):
        self.__qemu_exec = qemu_exec
        self.__kvm_enabled = kvm_enabled
        self.__host_name = host_name

    def get_hypervisor_name(self):
        return "qemu-system-x86"
    
    def create_img(self, base_img_path, img_path):
        cmd = ["qemu-img create",
               "-b {}".format(base_img_path),
               "-f qcow2",
               "{}".format(img_path)]
        print cmd
	return cmd

        
    def start_vm(self, vm):
        # Construct command for starting vm
        cmd = ["{}".format(self.__qemu_exec)]
        cmd.append("-daemonize")
        cmd.append("-vnc none")

        # KVM
        if self.__kvm_enabled:
            cmd.append("-enable-kvm")

        cmd.append("-m {}".format(vm.ram_size))
        
        # KVM
        if self.__kvm_enabled:
            cmd.append("-cpu host")
        cmd.append("-smp cores={},threads={},sockets={}".format(vm.cpu_cores, vm.cpu_threads, vm.cpu_sockets))
        
        #cmd.append("-net nic,macaddr={},model=virtio".format(vm.mac_adder))

        # Network
        if vm.network_mode == 2:
            for port in vm.listen_port:
                cmd.append("-net socket,listen=:{}".format(port))
            i = 0
            for port in vm.connect_port:
                host = vm.connect_host[i]
                cmd.append("-net socket,connect={}:{}".format(host, port))
                i = i + 1
        else:
            #cmd.append("-net socket,mcast=230.0.0.1:{}".format(vm.mcast_port))
            cmd.append("-netdev socket,id=net,mcast=230.0.0.1:{}".format(vm.mcast_port))
            cmd.append("-device virtio-net-pci,netdev=net,mac={}".format(vm.mac_adder))
        
        #cmd.append("-net nic,vlan=1 -net user,vlan=1,hostfwd=tcp::{}-:22".format(vm.ssh_port))
        cmd.append("-netdev user,id=net0,hostfwd=tcp::{}-:22".format(vm.ssh_port))
        cmd.append("-device virtio-net-pci,netdev=net0")

        cmd.append("-qmp tcp:{}:{},server,nowait".format(self.__host_name, 6666))
        
        # Storage
        #cmd.append("-hda {}".format(vm.img))
        cmd.append("-drive file={},cache=none,if=virtio".format(vm.img))

        if vm.storage_mode == 3: # virtual IO
        	#cmd.append("-fsdev local,security_model=none,id=fsdev0,path={}".format(vm.host_shared_dir))
                cmd.append("-fsdev local,security_model=none,id=fsdev0,path={}".format(vm.host_shared_dir))
        	cmd.append("-device virtio-9p-pci,id=fs0,fsdev=fsdev0,mount_tag={}".format(vm.mount_tag))
        if vm.storage_mode == 1 and vm.get_hostname() == vm.master.get_hostname(): # data img + nfs
        	cmd.append("-hdb {}".format(vm.data_img))

        vm.status = 'Running'
	print cmd
        return cmd
        

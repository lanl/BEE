# system
from termcolor import cprint


class Hypervisor(object):
    def add_vm(self, vm):
        pass

    def get_vm_list(self):
        pass

    def remove_vm(self, vm):
        pass

    def start_vm(self, vm):
        pass

    def stop_vm(self, vm):
        pass

    def query_vm(self, vm):
        pass


class QEMU(Hypervisor):
    def __init__(self, host_name, qemu_exec, kvm_enabled):
        self.__qemu_exec = qemu_exec
        self.__kvm_enabled = kvm_enabled
        self.__host_name = host_name
        self.__pexpect_child = ""
        self.__vm = ""
        self.__output_color = "green"

        self.hypervisor_name = "qemu-system-x86"

    @staticmethod
    def create_img(base_img_path, img_path):
        cmd = ["qemu-img create",
               "-b {}".format(base_img_path),
               "-f qcow2",
               "{}".format(img_path)]
        return cmd

    def start_vm(self, vm):
        # Save vm info
        self.__vm = vm

        # Construct command for starting vm
        cmd = ["{}".format(self.__qemu_exec), "-vnc none"]

        # KVM
        if self.__kvm_enabled:
            cmd.append("-enable-kvm")
        cmd.append("-m {}".format(vm.ram_size))

        # KVM
        if self.__kvm_enabled:
            cmd.append("-cpu host")
        cmd.append("-smp cores={},threads={},sockets={}".format(vm.cpu_cores, vm.cpu_threads, vm.cpu_sockets))

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
            cmd.append("-netdev socket,id=net,mcast=230.0.0.1:{}".format(vm.mcast_port))
            cmd.append("-device virtio-net-pci,netdev=net,mac={}".format(vm.mac_adder))

        cmd.append("-netdev user,id=net0,hostfwd=tcp::{}-:22".format(vm.ssh_port))
        cmd.append("-device virtio-net-pci,netdev=net0")
        cmd.append("-qmp tcp:{}:{},server,nowait".format(self.__host_name, 6666))

        # Storage
        cmd.append("-drive file={},cache=none,if=virtio".format(vm.img))

        if vm.storage_mode == 3:  # virtual IO
            cmd.append("-fsdev local,security_model=none,id=fsdev0,path={}".format(vm.host_shared_dir))
            cmd.append("-device virtio-9p-pci,id=fs0,fsdev=fsdev0,mount_tag={}".format(vm.mount_tag))
        if vm.storage_mode == 1 and vm.get_hostname() == vm.master.get_hostname():  # data img + nfs
            cmd.append("-hdb {}".format(vm.data_img))

        # Qemu monitoring
        cmd.append("-monitor stdio")
        vm.status = 'Running'
        return cmd

    def checkpoint_vm(self):
        cprint("qemu.checkpoint_vm not implemented", 'yellow')

    def restore_vm(self):
        cprint("qemu.restore_vm not implemented", 'yellow')

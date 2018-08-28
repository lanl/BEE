from bee_vm import BeeVM
from host import Host
from docker import Docker
import time
import subprocess
import os
import getpass
from os.path import expanduser
from threading import Thread
from threading import Event
from bee_task import BeeTask


class BeeVMLauncher(BeeTask):
    def __init__(self, task_id, beefile, restore = False):
        BeeTask.__init__(self)

        self.__platform = 'BEE-VM'
        
        self.__current_status = 0 # initializing
        
        # User configuration
        self.__task_conf = beefile['task_conf']
        self.__bee_vm_conf = beefile['exec_env_conf']['bee_vm']
        self.__docker_conf = beefile['docker_conf']
        self.__hosts = self.__bee_vm_conf['node_list']
        self.__task_name = self.__task_conf['task_name']
        self.__task_id = task_id

        # System configuration
        self.__user_name = getpass.getuser()
        self.__bee_working_dir = expanduser("~") + "/.bee"
        self.__vm_key_path = self.__bee_working_dir + "/ssh_key/id_rsa"
        self.__base_img_path = self.__bee_working_dir + "/base_img/base_img"
        self.__base_data_img_path = self.__bee_working_dir + "/base_img/base_data_img"
        self.__data_img_path = "data.qcow2"
        self.__vm_img_dir = self.__bee_working_dir + "/vm_imgs"
        self.__tmp_dir = self.__bee_working_dir + "/tmp"
        self.__restore = restore

        # bee-vms
        self.__bee_vm_list = []
        
        # Events for workflow
        self.__begin_event = Event()
        self.__end_event = Event()
        self.__event_list = []

        
        self.__current_status = 1 # initialized

    
    def get_begin_event(self):
        return self.__begin_event

    def get_end_event(self):
        return self.__end_event

    def add_wait_event(self, new_event):
        self.__event_list.append(new_event)

    def get_current_status(self):
        return self.__current_status

    def get_platform(self):
        return self.__platform

    def run(self):
        self.launch()

    def launch(self):
        self.terminate(clean = True)
        self.__current_status = 3 # Launching
        
        #self.kill_all()
        network_mode = 1
        storage_mode = 3

        for host in self.__hosts:
            curr_rank = len(self.__bee_vm_list)
            
            img_path = "{}/img_{}_{}.qcow2".format(self.__vm_img_dir, self.__task_name, curr_rank)
            
            hostname = ""
            if curr_rank == 0:
                hostname = "{}-bee-master".format(self.__task_name)
            else:
                hostname = "{}-bee-worker{}".format(self.__task_name, str(curr_rank).zfill(3))
    
            bee_vm = BeeVM(self.__task_id, hostname, host, curr_rank, 
                           self.__task_conf, self.__bee_vm_conf, 
                           self.__vm_key_path, self.__base_img_path, img_path, network_mode, storage_mode)
            
            # Add new VM to host
            self.__bee_vm_list.append(bee_vm)
            bee_vm.set_master(self.__bee_vm_list[0])

        #if network_mode == 1:
        # <no extra work need to be done>   
            
        if network_mode == 2:
            star = False
            tree = True
            # P2P Configure network
            if star:
                for i in range(1,  len(self.hosts)):
                    self.__bee_vm_list[0].connect_to_me(self.__bee_vm_list[i]) 
            if tree:
                self.__bee_vm_list[0].connect_to_me(self.__bee_vm_list[1])
                #self.__bee_vm_list[0].connect_to_me(self.__bee_vm_list[2])
                #self.__bee_vm_list[0].connect_to_me(self.__bee_vm_list[3])
                #self.__bee_vm_list[1].connect_to_me(self.__bee_vm_list[4])
                #self.__bee_vm_list[1].connect_to_me(self.__bee_vm_list[5])
                #self.__bee_vm_list[1].connect_to_me(self.__bee_vm_list[6])
                #self.__bee_vm_list[1].connect_to_me(self.__bee_vm_list[7])
                #self.__bee_vm_list[2].connect_to_me(self.__bee_vm_list[8])
                #self.__bee_vm_list[2].connect_to_me(self.__bee_vm_list[9])
                #self.__bee_vm_list[2].connect_to_me(self.__bee_vm_list[10])
                #self.__bee_vm_list[2].connect_to_me(self.__bee_vm_list[11])
                #self.__bee_vm_list[3].connect_to_me(self.__bee_vm_list[12])
                #self.__bee_vm_list[3].connect_to_me(self.__bee_vm_list[13])
                #self.__bee_vm_list[3].connect_to_me(self.__bee_vm_list[14])
                #self.__bee_vm_list[3].connect_to_me(self.__bee_vm_list[15])
        
        if storage_mode == 1:
            self.__bee_vm_list[0].set_data_img(base_data_img_path, data_img_path)
            self.__bee_vm_list[0].create_data_img()
        
        # if restoring use old OS images, otherwise create new ones
        if not self.__restore:
            for bee_vm in self.__bee_vm_list:
                bee_vm.create_os_img()
            

        # Start VMs
        for bee_vm in self.__bee_vm_list:
            bee_vm.start()
        
        time.sleep(60)

        if self.__restore:
            for bee_vm in self.__bee_vm_list:
                bee_vm.restore()
                
        # Setup hostname
        for bee_vm in self.__bee_vm_list:
            bee_vm.set_hostname()

        # Setup hosts file
        for host1 in self.__bee_vm_list:
            for host2 in self.__bee_vm_list:
                host2.add_host_list(host1.get_ip(), host1.get_hostname())

        # Setup storage
        if storage_mode == 1:
            self.__bee_vm_list[0].mount_data_img()
            workers = self.__bee_vm_list[1:]
            for bee_vm in workers:
                bee_vm.mount_master_data_img()
        if storage_mode == 2:
            for bee_vm in self.__bee_vm_list:
                self.__bee_vm_list.mount_nfs("ccs7-isilon2-10gige.darwin:/ifs/data/darwin_home/jieyangchen/vmshare2")
        if storage_mode == 3:
            for bee_vm in self.__bee_vm_list:
                bee_vm.mount_virtio()

        for bee_vm in self.__bee_vm_list:
            bee_vm.update_uid()
            bee_vm.update_gid()
            bee_vm.update_ownership()
            bee_vm.update_mtu()

        print "vm conf done"
        time.sleep(20)

        self.configure_dockers()
        self.wait_for_others()
        self.run_scripts()
        
        if self.__task_conf['terminate_after_exec']:
            self.terminate()
	print "docker conf done"

    def configure_dockers(self):
        for bee_vm in self.__bee_vm_list:
            docker = Docker(self.__docker_conf)
            bee_vm.add_docker_container(docker)
        # Get Dockers ready in parallel
        self.__bee_vm_list[0].get_docker_img(self.__bee_vm_list)
        for bee_vm in self.__bee_vm_list:
            bee_vm.start_docker("/usr/sbin/sshd -D")
            bee_vm.docker_update_uid()
            bee_vm.docker_update_gid()



    def wait_for_others(self):
        self.__current_status = 2 # Waiting  
        # wait for other tasks
        for event in self.__event_list:
            event.wait()

    def run_scripts(self):
        self.__current_status = 4 #Running
        # set out flag as begin launching
        self.__begin_event.set()
        if self.__task_conf['batch_mode']:
            self.batch_run()
        else:
            self.general_run()
        self.__current_status = 5 # finished
        # set out flag as finish launching
        self.__end_event.set()


    def general_run(self):
        # General sequential script
        master = self.__bee_vm_list[0]
        
        for run_conf in self.__task_conf['general_run']:
            host_script_path = run_conf['script']
            vm_script_path = '/home/ubuntu/general_script.sh'

            docker_script_path = ''
            if (self.__docker_conf['docker_username'] == 'root'):
                docker_script_path = '/root/general_script.sh'
            else:
                docker_script_path = '/home/{}/general_script.sh'.format(self.__docker_conf['docker_username'])
                for bee_vm in self.__bee_vm_list:
                    bee_vm.docker_seq_run('cp -r /home/{}/.ssh /root/'.format(self.__docker_conf['docker_username']))

            master.copy_file(host_script_path, vm_script_path)
            master.docker_copy_file(vm_script_path, docker_script_path)
            master.docker_seq_run(docker_script_path, local_pfwd = run_conf['local_port_fwd'],
                                  remote_pfwd = run_conf['remote_port_fwd'], async = False)

        for run_conf in self.__task_conf['mpi_run']:
            host_script_path = run_conf['script']
            vm_script_path = '/home/ubuntu/mpi_script.sh'

            docker_script_path = ''
            hostfile_path = ''
            if (self.__docker_conf['docker_username'] == 'root'):
                docker_script_path = '/root/mpi_script.sh'
                hostfile_path = '/root/hostfile'
            else:
                docker_script_path = '/home/{}/mpi_script.sh'.format(self.__docker_conf['docker_username'])
                hostfile_path = '/home/{}/hostfile'.format(self.__docker_conf['docker_username'])
                for bee_vm in self.__bee_vm_list:
                    bee_vm.docker_seq_run('cp -r /home/{}/.ssh /root/'.format(self.__docker_conf['docker_username']))
			

            for bee_vm in self.__bee_vm_list:
                bee_vm.copy_file(host_script_path, vm_script_path)
                bee_vm.docker_copy_file(vm_script_path, docker_script_path)
            
            # Generate hostfile and copy to container
            master.docker_make_hostfile(run_conf, self.__bee_vm_list, self.__tmp_dir)
            master.copy_file(self.__tmp_dir + '/hostfile', '/home/ubuntu/hostfile')
            master.docker_copy_file('/home/ubuntu/hostfile', hostfile_path)
            # Run parallel script on all nodes
            master.docker_para_run(run_conf,
                                   docker_script_path, 
                                   hostfile_path, 
                                   local_pfwd = run_conf['local_port_fwd'],
                                   remote_pfwd = run_conf['remote_port_fwd'],
                                   async = False)


    def batch_run(self):
        run_conf_list = self.__task_conf['general_run']
        if len(run_conf_list) != len(self.__bee_vm_list):
            print("[Error] Scripts and BEE-VM not match in numbers!")
        popen_list = []
        count = 0
        for run_conf in run_conf_list:
            bee_vm = self.__bee_vm_list[count]
            count = count + 1
            host_script_path = run_conf['script']
            vm_script_path = '/home/ubuntu/general_script.sh'

            docker_script_path = ''
            if (self.__docker_conf['docker_username'] == 'root'):
                docker_script_path = '/root/general_script.sh'
            else:
                docker_script_path = '/home/{}/general_script.sh'.format(self.__docker_conf['docker_username'])

            bee_vm.copy_file(host_script_path, vm_script_path)
            bee_vm.docker_copy_file(vm_script_path, docker_script_path)
            p = bee_vm.docker_seq_run(docker_script_path, local_pfwd = run_conf['local_port_fwd'],
                                      remote_pfwd = run_conf['remote_port_fwd'], async = True)
            popen_list.append(p)
        for popen in popen_list:
            popen.wait()
            

    def checkpoint(self):
        for bee_vm in self.__bee_vm_list:
            bee_vm.checkpoint()

    def restore(self):
        for bee_vm in self.__bee_vm_list:
            bee_vm.restore()

    def terminate(self, clean = False):
        for host in self.__hosts:
            h = Host(host)
            h.kill_all_vms()
            if not clean:
                self.__current_status = 6 #Terminated

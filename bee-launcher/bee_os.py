import subprocess
from docker import Docker
import os
from termcolor import colored, cprint
import time

class BeeOS(object):
    def __init__(self, task_id, hostname, rank, task_conf, bee_os_conf, key_path, private_ip, master_public_ip, master = ""):
        # Basic configurations
        self.status = ""
        self.hostname = hostname
        self.__rank = rank
        self.master = master
        self.__user_name = "cc"
        self.__key_path = key_path
        self.__remote_key_path = '/home/cc/.ssh/id_rsa'
        self.__instance_share_dir = '/exports/host_share'

        # Network
        self.private_ip = private_ip
        self.master_public_ip = master_public_ip


        # Docker container
        self.__docker = ""

        self.__output_color = "cyan"

    def run_on_master(self, command, local_pfwd = [], remote_pfwd = [], async = False):
        exec_cmd = ["ssh",
                    "-o StrictHostKeyChecking=no",
                    "-o ConnectTimeout=300",
                    "-o UserKnownHostsFile=/dev/null",
                    "-i {}".format(self.__key_path),
                    "{}@{}".format(self.__user_name, self.master_public_ip),
                    "-x"]
        for port in local_pfwd:
            exec_cmd.insert(7, "-L {}:localhost:{}".format(port, port))
        for port in remote_pfwd:
            exec_cmd.insert(7, "-R {}:localhost:{}".format(port, port))

        cmd = exec_cmd + command

        print(' '.join(cmd))
        if async:
            return Popen(' '.join(cmd))
        else:
            return subprocess.call(' '.join(cmd), shell = True)


    def run_on_worker(self, command, local_pfwd = [], remote_pfwd = [], async = False):
        exec_cmd = ["ssh",
                    "-o StrictHostKeyChecking=no",
                    "-o ConnectTimeout=300",
                    "-o UserKnownHostsFile=/dev/null",
                    "-i {}".format(self.__remote_key_path),
                    "{}@{}".format(self.__user_name, self.private_ip),
                    "-x"]
        for port in local_pfwd:
            exec_cmd.insert(7, "-L {}:localhost:{}".format(port, port))
        for port in remote_pfwd:
            exec_cmd.insert(7, "-R {}:localhost:{}".format(port, port))

        cmd = exec_cmd + command
        self.master.run_on_master(cmd, local_pfwd, remote_pfwd, async)

    def run(self, command, local_pfwd = [], remote_pfwd = [], async = False):
        if (self.master == ""):
            # this is the master node
            self.run_on_master(command, local_pfwd, remote_pfwd, async)
        else:
            # this is one of the worker nodes
            self.run_on_worker(command, local_pfwd, remote_pfwd, async)

    def parallel_run(self, command, nodes, local_pfwd = [], remote_pfwd = [], async = False):
        cmd = ["mpirun",
             "--mca btl_tcp_if_include eno1",
               "-host"]
        node_list = ""
        for node in nodes:
            node_name = node.get_hostname()
            node_list = node_list + node_name + ","
        cmd.append(node_list)
        cmd = cmd + command        
        return self.run(cmd, local_pfwd = local_pfwd, remote_pfwd = remote_pfwd, async = async)

    def copy_to_master(self, src, dest):
        cprint("["+self.hostname+"]: copy file to master: "+src+" --> "+dest+".", self.__output_color)
        cmd = ["scp",
               "-i {}".format(self.__key_path),
               "-o StrictHostKeyChecking=no",
               "-o ConnectTimeout=300",
               "-o UserKnownHostsFile=/dev/null",
               "{}".format(src),
               "{}@{}:{}".format(self.__user_name, self.master_public_ip, dest)]
        print(' '.join(cmd))
        subprocess.call(' '.join(cmd), shell = True)

    def copy_to_worker(self, src, dest, worker):
        cprint("["+self.hostname+"]: copy file to worker: "+ src +" --> "+dest +".", self.__output_color)
        cmd = ["scp",
               "-i {}".format(self.__remote_key_path),
               "-o StrictHostKeyChecking=no",
               "-o ConnectTimeout=300",
               "-o UserKnownHostsFile=/dev/null",
               "{}".format(src),
               "{}@{}:{}".format(self.__user_name, worker.private_ip, dest)]
        self.run_on_master(cmd)

    def copy_from_master(self, src, dest):
        cprint("["+self.hostname+"]: copy file from master: "+src+" --> "+dest+".", self.__output_color)
        cmd = ["scp",
               "-i {}".format(self.__key_path),
               "-o StrictHostKeyChecking=no",
               "-o ConnectTimeout=300",
               "-o UserKnownHostsFile=/dev/null",
               "{}@{}:{}".format(self.__user_name, self.master_public_ip, src),
               "{}".format(dist)]
               
        print(' '.join(cmd))
        subprocess.call(' '.join(cmd), shell = True)

    def get_ip(self):
        return self.private_ip    

    def get_hostname(self):
        return self.hostname

    def set_hostname(self):
        cprint("["+self.hostname+"]: set hostname.", self.__output_color)
        cmd = ["sudo hostname", self.hostname]
        self.run(cmd)

    def add_host_list(self, private_ip, hostname):
        cprint("["+self.hostname+"]: set hosts file for MPI.", self.__output_color)
        cmd = ["sudo echo",
               "\"{} {}\"".format(private_ip, hostname),
               "|",
               "ssh",
               "{}@{}".format(self.__user_name, self.private_ip),
               "\"sudo tee --append /etc/hosts\""]
        self.run(["'"] + cmd + ["'"])

    def set_nfs_master(self):
        cprint("["+self.hostname+"]: set NFS on master.", self.__output_color)
        cmd = ["sudo mkdir",
               "-p",
               "{}".format(self.__instance_share_dir)]
        self.run(cmd)

        cmd = ["sudo chown",
               "-R",
               "cc:cc",
               "{}".format(self.__instance_share_dir)]
        self.run(cmd)

        cmd = ["sudo echo",
               "\"{} 10.140.80.0/22(rw,async) 10.40.0.0/23(rw,async)\"".format(self.__instance_share_dir),
               "|",
               "ssh",
               "{}@{}".format(self.__user_name, self.private_ip),
               "\"sudo tee --append /etc/exports\""]
        self.run(["'"] + cmd + ["'"])

        cmd = ["sudo exportfs -a"]
        self.run(cmd)

    def set_nfs_worker(self, master_private_ip):
        cprint("["+self.hostname+"]: set NFS on worker.", self.__output_color)
        cmd = ["sudo mkdir",
               "-p",
               "{}".format(self.__instance_share_dir)]
        self.run(cmd)

        cmd = ["sudo chown",
               "-R",
               "cc:cc",
               "{}".format(self.__instance_share_dir)]
        self.run(cmd)

        cmd = ["sudo echo",
               "\"{}:{}    {}    nfs\"".format(master_private_ip, self.__instance_share_dir, self.__instance_share_dir),
               "|",
               "ssh",
               "{}@{}".format(self.__user_name, self.private_ip),
               "\"sudo tee --append /etc/fstab\""]
        self.run(["'"] + cmd + ["'"])

        cmd = ["sudo mount -a"]
        self.run(cmd)

    def set_file_permssion(self, path):
        cmd = ["sudo chmod",
               "766",
               "{}".format(path)]
        self.run(cmd)
        

    def add_docker_container(self, docker):
        self.__docker = docker

    def get_docker_img(self, nodes):
        cprint("["+self.hostname+"]: pull docker image in parallel.", self.__output_color)
        self.parallel_run(['sudo'] + self.__docker.get_docker_img(), nodes)

    def start_docker(self, exec_cmd):
        cprint("["+self.hostname+"]: start docker container.", self.__output_color)
        self.run(['sudo'] + self.__docker.start_docker(exec_cmd)) 

    def docker_copy_file(self, src, dest):
        cprint("["+self.hostname+"][Docker]: copy file to docker " + src + " --> " + dest +".", self.__output_color)
        self.run(['sudo'] + self.__docker.copy_file(src, dest))
        self.run(['sudo'] + self.__docker.update_file_ownership(dest))

    def docker_copy_file_out(self, src, dest):
        cprint("["+self.hostname+"][Docker]: copy file from docker " + src + " --> " + dest +".", self.__output_color)
        self.run(['sudo'] + self.__docker.copy_file_out(src, dest))

    def docker_seq_run(self, exec_cmd, local_pfwd = [], remote_pfwd = [], async = False):
        cprint("["+self.hostname+"][Docker]: run script:"+exec_cmd+".", self.__output_color)
        self.run(['sudo'] + self.__docker.run([exec_cmd]), local_pfwd = local_pfwd, remote_pfwd = remote_pfwd, async = async)

    def docker_para_run(self, run_conf, exec_cmd, hostfile_path, local_pfwd = [], remote_pfwd = [], async = False):
        cprint("["+self.hostname+"][Docker]: run parallel script:" + exec_cmd + ".", self.__output_color)
        np = int(run_conf['proc_per_node']) * int(run_conf['num_of_nodes'])
        cmd = ["mpirun",
               "--allow-run-as-root",
               "--mca btl_tcp_if_include eno1",
               "--hostfile {}".format(hostfile_path),
               "-np {}".format(np)]
        cmd = cmd + [exec_cmd]
        self.run(['sudo'] + self.__docker.run(cmd), local_pfwd = local_pfwd, remote_pfwd = remote_pfwd, async = async)

    def docker_para_run_scalability_test(self, run_conf, exec_cmd, hostfile_path, local_pfwd = [], remote_pfwd = [], async = False):
        cprint("["+self.hostname+"][Docker]: run parallel script:" + exec_cmd + ".", self.__output_color)
        np = int(run_conf['proc_per_node']) * int(run_conf['num_of_nodes'])
        cmd = ["mpirun",
               "--allow-run-as-root",
               "--mca btl_tcp_if_include eno1",
               "--hostfile {}".format(hostfile_path),
               "-np {}".format(np)]
        cmd = cmd + [exec_cmd] + [">>", "bee_scalability_test_{}_{}_.output".format(str(run_conf['num_of_nodes']).zfill(3), str(run_conf['proc_per_node']).zfill(3))]
        self.run(['sudo'] + self.__docker.run(cmd), local_pfwd = local_pfwd, remote_pfwd = remote_pfwd, async = async)

    def docker_make_hostfile(self, run_conf, nodes, tmp_dir):
        cprint("["+self.hostname+"][Docker]: prepare hostfile.", self.__output_color)
        hostfile_path = "{}/hostfile".format(tmp_dir)
        # Remove old hostfile
        cmd = ["rm",hostfile_path]
        subprocess.call(' '.join(cmd), shell = True)
        # Create new hostfile
        cmd = ["touch", hostfile_path]
        subprocess.call(' '.join(cmd), shell = True)
        # Add nodes to hostfile
        for i in range(int(run_conf['num_of_nodes'])):
            cmd = ["echo",
                   "\"{} slots={} \"".format(nodes[i].get_hostname(), run_conf['proc_per_node']),
                   "|",
                   "tee -a",
                   hostfile_path]
            print(' '.join(cmd))
            subprocess.call(' '.join(cmd), shell = True)

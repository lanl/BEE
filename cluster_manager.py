from cluster import Cluster
from host import Host
class ClusterManager(object):
    def __init__(self):
        #active hosts stores hosts that are already initialized
        self.active_hosts = dict()
        self.cluster_list = dict()
        
    def create_cluster(self, name, host_names, hostshare_dir, dockershare_dir, docker_tag, docker_user):
        print("Cluster Manager: received create cluster request")
        
        #group hosts into a list
        host_list = []
        for host_name in host_names:
            if not host_name in self.active_hosts:
                host = Host(host_name)
                self.active_hosts[host_name] = host
                
            host_list.append(self.active_hosts[host_name])
        
        #create a new cluster
        cluster = Cluster(name, host_list)

        #initialize the new cluster
        cluster.initialize(hostshare_dir, dockershare_dir, docker_tag, docker_user)

        #finish initialization, add cluster to list
        self.cluster_list[name] = cluster

    def start_cluster(self, name):
        cluster = self.cluster_list[name]
        cluster.start()

    def stop_cluster(self, name):
        cluster = self.cluster_list[name]
        cluster.stop()

    def remove_cluster(self, name):
        cluster = self.cluster_list[name]
        cluster.distroy()
        self.cluster_list.pop(name)

    def get_cluster_list(self):
        return self.cluster_list;

    def force_stop_all(self, hosts):
        
        for host_name in hosts:
            host = Host(host_name)
            host.kill_all_vms()
            

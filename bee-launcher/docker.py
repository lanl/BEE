class Docker(object):
    def __init__(self, docker_conf):
        
        self.__docker_img_tag = docker_conf['docker_img_tag']
        self.__docker_username = docker_conf['docker_username']
        self.__docker_shared_dir = docker_conf['docker_shared_dir']

        self.__dockerfile_git_url = ""
        self.__dockerfile_path = ""
        
        self.__docker_container_name = "bee_docker"
        self.__vm_shared_dir = "/home/ubuntu/vmshare"

    def get_dockerfile(self):
        # Get Dockerfile from git repository.
        cmd = ["git",
               "clone",
               "{}".format(dockerfile_git_url)]

        # Resolve repository folder name.
        self.__dockerfile_path = dockerfile_git_url.split("/")[-1].split(".")[0]
        self.__docker_img_tag = __dockerfile_path
        return cmd

    def get_docker_img(self):        
        # Get Docker image fron DockerHub.
        cmd = ["docker",
               "pull",
               "{}".format(self.__docker_img_tag)]
        return cmd
        
    def build_docker(self):
        # Build Docker image from dockerfile.
        # This step is only necessary if we get dockerfile not docker image.
        cmd = ["docker",
               "build",
               "-t=\"{}\"".format(self.__docker_img_tag),
               "./{}".format(self.__dockerfile_path)]
        return cmd

    def start_docker(self, exec_cmd):
        # Start the Docker with given command (i.e. exec_cmd).
        cmd = ["docker",
               "run",
               "--name {}".format(self.__docker_container_name),
               "--net=host",
               "-d",
               "-v {}:{}".format(self.__vm_shared_dir, self.__docker_shared_dir),
               "{}".format(self.__docker_img_tag),
               "{}".format(exec_cmd)]

        return cmd

    def run(self, exec_cmd):
        #execute command on the running Docker container
        cmd = ["docker",
               "exec",
               "{}".format(self.__docker_container_name)]
        cmd = cmd + exec_cmd
        return cmd
        
    def update_uid(self, uid):
        # Change user's UID to match host's UID.  
        # This is necessary for dir sharing. 
        cmd = ["usermod",
               "-u {} {}".format(uid, self.__docker_username)]
        return self.run(cmd)


    def update_gid(self, gid):
        # Change user's GID to match host's GID.                                                
        # This is necessary for dir sharing.
        cmd = ["groupmod",
               "-g {} {}".format(gid, self.__docker_username)]

        return self.run(cmd)


    def copy_file(self, src_path, dist_path):
        cmd = ["docker",
               "cp",
               "{}".format(src_path),
               "{}:{}".format(self.__docker_container_name, dist_path)]
        return cmd

## Build and Execute Environment (BEE) User Guide for building your own BEE-compatible Docker images

The following guide shows you how to build your own Docker images that can run on BEE.

### Using pre-built BEE Docker base image
The recommended way is building your Docker images based on pre-built BEE Docker base image (`cjy7117/ubuntu-ompi`). 
This pre-build has basic tools and packages installed including SSH server (with ssh keys) and OpenMPI (version 2.0.2).
A default standard user `beeuser` is created in this image, which is designed to run user applications. 
To share files between Docker containers on different nodes, a designated directory `/mnt/docker_share` is created.

When writting Dockerfiles, simply use the pre-built BEE Docker base image and be sure to set input/output directories under `/mnt/docker_share`.
If root is necessary to run your application, specify 'root' in the 'docker_user' section of Beefile. Otherwise, use 'beeuser' as default.
Push your Docker images to DockerHub and specify the tag name in 'docker_img_tag' section of Beefile. The 'docker_shared_dir' should leave as defult `/mnt/docker_share`.

### Building BEE-compatible Docker images from scratch
Building BEE-compatible Docker images from scratch is more complicated but provides more flexibility. 

#### If you need SSH connection between Docker containers, make sure to:

* Install SSH server and client.
* Setup SSH keypairs/authroized_keys.
* Disable strict host key checking.
* Avoid using defualt port `22` for SSH, since that port is reserved for SSH communication between hosts.

#### If you need to share files between Docker containers, make sure to:

* Create a directory specific for file sharing.
* Leave it blank, since its content will be replaced by files in the host share directory after launching.
* Make it accessible to the user you plan to run your application.

#### If your application cannot be run by root user, make sure to:

* Create a non-root user
* Setup ownership and read/write permissions for all you application-related files and the shared directory, if it exists.

#### How to fill in Beefiles for you Docker images:
In the 'docker_conf' section of Beefile:
* 'docker_img_tag' sepcifies your Docker image tag on DockerHub.
* 'docker_username' specifies the username inside the Docker container that is going to be used for running your application.
* 'docker_shared_dir' specifies the shared directory you created to share files between Docker containers.





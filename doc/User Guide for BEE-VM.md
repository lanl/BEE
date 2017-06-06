## Build and Execute Environment (BEE) User Guide for `BEE-VM`

The following guide shows you how to run `BEE-VM` on HPC environment.

#### Installation
##### Step 1. Install dependecies
If this is your first time using BEE, run `install.sh` first.

##### Step 2. Build BEE-VM image
Before using BEE to launch `BEE-VM` tasks, building BEE-VM images using the BEE Image Builder is necessary. The BEE-VM image only need to be build once. 
* (1) Download Packer binary [here](https://www.packer.io/downloads.html). Add Packer binary to `$PATH` environment variable, so that it can run anywhere. (You can skip this step if you already have Packer.)
* (2) `cd` into the `bee-image-builder` folder of this repo. Run `./build_bee_vm.sh` to build base image for `BEE-VM`. This step must be done on a QEMU-enabled machine and would usually take 10-20 minutes with KVM-enabled and longer time without KVM. 

##### Step 3. Add bee launcher to $PATH
Add the directory of bee-launcher to $PATH, so that it can run anywhere.    

#### Launch BEE-VM task

##### Step 1. Configure task file
Configure `<task_name>.beefile` file as follow:

* `task_conf`: specifiying configurations related to the task.
   * a. `task_name`: the name of the task to be execution. This has to be unique among all your tasks;
   * b. `exec_target`: execution target. It can be `bee_vm` or `bee_aws`;
   * b. `general_run`: list of scripts that will be run after launching;
     * b1. `script_path`: absuloate path to the script;
     * b2. `port_fwd`: port forwarding number using when running this script. `""` indicate no port forwarding used.
   * c. `mpi_run`: list of scripts that will be run in paralle by MPI after launching;
     * c1. `script_path`: absuloate path to the script;
     * c2. `port_fwd`: port forwarding number using when running this script. `""` indicate no port forwarding used;
     * c3. `num_of_nodes`: number of nodes needed to run target job;
     * c4. `proc_per_node`: number of processes per node needed to run target job;
* `docker_conf`: specifiying all configuration related to the docker image containing the target job.
  * a. `docker_img_tag`: the Docker image tag containing the target application on DockerHub;
  * b. `docker_username`: the user in Docker container used to run application;
  * c. `docker_shared_dir`: the directory inside Docker container that is shared among all Docker containers.
* `exec_env_conf`: specifiying all configuration related to the execution environment.
  * a. `bee_vm`: Execution configuration related to `BEE-VM`;
    * a1. `node_list`: list of nodes on HPC system allocated to run this job;
    * a2. `cpu_core_per_socket`: number of CPU cores per socket;
    * a3. `cpu_thread_per_core`: number of CPU thread per core;
    * a4. `cpu_sockets`: number of CPU sockets;
    * a5. `ram_size`: RAM size (512M, 8G, etc.);
    * a6. `kvm_enabled`: whether KVM is enabled or not;
    * a7. `host_input_dir`: input file directory.

##### Step 2. Launch task
* a. Prepare run scripts as necessary.
* b. Open `2` console windows. One serves as daemon control, another serves as client control.
* c. Run `bee_orc_ctl.py` on daemon control window to start Bee Launcher daemon. The daemon is necessary for keeping the launching, running, and monitoring process. So, running it in oridinary shell session could cause unexpected shutdown during to shell session timeout or disconnection. For long term exection, it is recommended to run the daemon on a separated `screen`. For details of using `screen`, please refer to [here](https://www.rackaid.com/blog/linux-screen-tutorial-and-how-to/)

* d. Run `bee_launcher.py` on client control window to launch Bee job. Several option let you launch, control and monotor tasks.
  * (1) `-l <task_name>`: runs task specified by <task_name>.beefile;
  * (2) `-s`: list all tasks with status;
  * (3) `-t <task_name>`: terminate task <task_name>;
  * (4) `-d <task_name>`: terminate and delete task <task_name> from task list;
  * (5) `-e <efs_name>`: create new efs with name <efs_name>.
   








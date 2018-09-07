## Build and Execute Environment (BEE) User Guide for `BEE-AWS`

The following guide shows you how to run `BEE-AWS` on AWS environment.

#### Installation
##### Step 1. Install dependecies
If this is your first time using BEE, run `install.sh` first.

##### Step 2. Build BEE-AWS image
Building AMI image is not necessary unless special customization is needed. Two pre-built general AMIs can be used:
* `ami-21232858`: HVM-based AMI (slower, more choices on instance type);
* `ami-ad5952d4`: Paravirtualized AMI (faster, less chioces on instance type).

To build BEE-AWS image:
* (1) Download Packer binary [here](https://www.packer.io/downloads.html). Add Packer binary to `$PATH` environment variable, so that it can run anywhere. (You can skip this step if you already have Packer.)
* (2) `cd` into the `bee-image-builder/bee-vm-and-aws-image-builder` folder of this repo. Run `./build_bee_aws.sh` to build base image for `BEE-AWS`.

##### Step 3. Add bee launcher to $PATH
Add the directory of bee-launcher to $PATH, so that it can run anywhere.    

##### Step 4. Configure AWS credentials and keys
(1) Get AWS access key pair from AWS. Create a `credentials` file in `~/.aws/`. Fill in the file as follow:
```
[default]
aws_access_key_id = <access_key_id>
aws_secret_access_key = <secret_access_key>

[default]
region = <aws_region>

```
(2) Get an AWS ssh key. Create a `sshkey.json` file in `~/.aws/`. Fill in the file as follow:
```
{
    "aws_key_name": "<key_name>",
    "aws_key_path": "<path_to_key>"
}
```

#### Launch BEE-VM task

##### Step 1. Configure task file
Configure `<task_name>.beefile` file as follow:

* `task_conf`: specifiying configurations related to the task.
   * a. `task_name`: the name of the task to be executed. This has to be unique among all your tasks;
   * b. `exec_target`: execution target. It can be `bee_vm` or `bee_aws`;
   * c. `batch_mode`: `true` or `false`. Turn on or off batch mode. For details, refer to `User Guide for Batch Mode`.
   * d. `general_run`: list of scripts that will be run after launching;
     * d1. `script`: name of the script. The script file need to be in current directory.
     * d2. `local_port_fwd`: list of port forwarding numbers (local --> BEE) to be used when running this script. `[]` indicates no port forwarding used.
     * d3. `remote_port_fwd`: list of port forwarding numbers (BEE --> local) to be used when running this script. `[]` indicates no port forwarding used.
   * e. `mpi_run`: list of scripts that will be run in parallel by MPI after launching;
     * e1. `script`: name of the script. The script file need to be in current directory.
     * e2. `local_port_fwd`: list of port forwarding numbers (local --> BEE) to be used when running this script. `[]` indicates no port forwarding used.
     * e3. `remote_port_fwd`: list of port forwarding numbers (BEE --> local) to be used when running this script. `[]` indicates no port forwarding used.
     * e4. `num_of_nodes`: number of nodes needed to run target job;
     * e5. `proc_per_node`: number of processes per node needed to run target job;
* `docker_conf`: specifiying all configuration related to the docker image containing the target job.
  * a. `docker_img_tag`: the Docker image tag containing the target application on DockerHub;
  * b. `docker_username`: the user in Docker container used to run application;
  * c. `docker_shared_dir`: the directory inside Docker container that is shared among all Docker containers.
* `exec_env_conf`: specifiying all configuration related to the execution environment.
  * a. `bee_aws`: Execution configuration related to `BEE-AWS`;
    * a1. `num_of_nodes`: number of node to run on AWS;
    * a2. `ami_image`: the AMI image used to launch `BEE-AWS`;
    * a3. `instance_type`: the AWS instance type;
    * a4. `efs_id`: the id of EFS that each AWS instance will mount to.

##### Step 2. Launch task
* a. Prepare run scripts as necessary.
* b. Open `2` console windows. One serves as daemon control, another serves as client control.
* c. Run `bee_orc_ctl.py` on daemon control window to start Bee Launcher daemon. The daemon is necessary for keeping the launching, running, and monitoring processes running. So, running it in ordinary shell session could cause unexpected shutdown due to shell session timeout or disconnection. For long term execution, it is recommended to run the daemon on a separated `screen`. For details of using `screen`, please refer to [here](https://www.rackaid.com/blog/linux-screen-tutorial-and-how-to/)

* d. Run `bee_launcher.py` on client control window to launch Bee job. Several options let you launch, control and monitor tasks.
  * (1) `-l <task_name>`: runs task specified by <task_name>.beefile, which need to be in the current directory;
  * (2) `-s`: list all tasks with status, automatically updates status;;
  * (3) `-t <task_name>`: terminate task <task_name>;
  * (4) `-d <task_name>`: terminate and delete task <task_name> from task list;
  * (5) `-e <efs_name>`: create new efs with name <efs_name>.
   








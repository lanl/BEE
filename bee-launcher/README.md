## Build and Execute Environment (BEE) User Guide
#### 1. BEE Image Builder
BEE Image Builder is used to build varity kinds of images for BEE, including VM images for `BEE-VM` and AMI images for `BEE-AWS`. It must be done before using BEE. Instructions to use BEE Image Builder are as follow:

##### Step 1. Get Packer
Download Packer binary [here](https://www.packer.io/downloads.html). Add Packer binary to `$PATH` environment variable, so that it can be called in command line.

##### Step 2. Get BEE Image Builder
Checkout the BEE Image Builder from repo [here](https://gitlab.lanl.gov/BEE/packer-qemu/tree/dev-ic) (`dev-ic` branch).
##### Step 3. Build Images
First, `cd` into the BEE Image Builder folder. 
* (1) run `./build_bee_vm.sh` to build base image for `BEE-VM` (It must be build for each HPC platform.)
* (2) run `./build_bee_aws.sh` to build base image for `BEE-AWS` (Pre-built general AMI  can be used, so that building AMI image is not necessary unless special customization is needed.)

Pre-built AMIs:
* `ami-bab826da`: HVM-based AMI (slower, more choices on instance type);
* `ami-908e15f0`: Paravirtualized AMI (faster, less chioces on instance type).


#### 2. BEE Launcher
##### Step 1. Get BEE Launcher
Checkout the BEE Launcher from repo [here](https://gitlab.lanl.gov/BEE/BEE_Launcher_Integration).

##### Step 2. Setup AWS Credentials
Create a file under your home directory `~/.aws/credentials`.
Fill in the credential information as follow:
````
[default]
aws_access_key_id = <ACCESS_KEY>
aws_secret_access_key = <SECRET_KEY>
region = <REGION>
````

##### Step 3. Install required libraries
* PYRO4 is necessary to the daemon-client structure of Bee Launcher. To install PYRO, run command: `pip install pyro4 --user` Then, run `./start_ns.sh` on daemon control window to start PYRO name server.
* Boto3 is necessary for `BEE-AWS`. To install Boto, run command: `pip install boto3 --user`.

##### Step 4. Configure BEE Launcher
First, `cd` into the BEE Launcher folder and configure `bee-config.json` file:

* `job_conf`: specifiying all configuration related to target job.
	 * a. `exec_target`: execution target. It can be `bee-vm` or `bee-aws`;
	 * b. `seq_run_script`: execution script that will be run in Docker container *sequentially*;
	 * c. `para_run_script`: execution script that will be run in Docker container *parallelized*;
	 * d. `num_of_nodes`: number of nodes needed to run target job;
	 * e. `proc_per_node`: number of processes per node needed to run target job;

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
	* b. `bee_aws`: Execution configuration related to `BEE-AWS`;
		* b1. `ami_image`: the AMI image used to launch `BEE-AWS`;
		* b2. `aws_key_path`: the path to the AWS key;
		* b3. `aws_key_name`: the AWS key name;
		* b4. `instance_type`: the AWS instance type.

##### Step 5. Use BEE Launcher
###### a. Prepare run scripts as necessary.
###### b. Open `2` console windows. One serves as daemon control, another serves as client control.
###### c. Run `./bee_launcher_daemon.py` on daemon control window to start Bee Launcher daemon.
###### d. Run `./bee_launcher.py` on client control window to launch Bee job.







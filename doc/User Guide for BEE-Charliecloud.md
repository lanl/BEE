## Build and Execute Environment (BEE) User Guide for `BEE-Charliecloud`

The following guide shows you how to run `BEE-Charliecloud` on HPC environment.

### Installation
##### Step 1. Install dependecies
If this is your first time using BEE, run `install.sh` first.

##### Step 2. Add bee launcher to $PATH
Add the directory of bee-launcher to $PATH, so that it can run anywhere.    

### Launch BEE-Charliecloud task

##### Step 1. Configure task (beefile) file
Configure `<task_name>.beefile` file as follow:

* `task_conf`: specifiying configurations related to the task.
   * a. `task_name`: name of task to be executed; should be unique
         and the same as the beefile;

   * b. `exec_target`: execution target; `bee-charliecloud`;

   * c. `batch_mode`: `true` or `false`; For details, 
            refer to `User Guide for Batch Mode`.

   * d. `general_run`: list of scripts that will be run after launching;
     * 1. `script`: name of the script. The script file needs to be in current
            directory.
     * 2. `local_port_fwd`: list of port forwarding numbers (local --> BEE) 
             to be used when running this script. `[]` indicates no port 
             forwarding used.
     * 3. `remote_port_fwd`: list of port forwarding numbers (BEE --> local) 
           to be used when running this script. 
           `[]` indicates no port forwarding used.

   * e. `mpi_run`: list of scripts that will be run in parallel by MPI after 
         launching;
     * 1. `script`: name of the script. The script file needs to be in current
            directory.
     * 2. `node_list`: node names i.e. ["cn30", "cn31" ...] to run target job on;
     * 3. `map_by`: (optional)
            map_by flag for mpirun command i.e. "node" or "core", invalid if 
            no map_num
     * 4. `map_num`:  argument to map_by flag.

* `container_conf`: Charliecloud container info.
  * a. `container_path`: entire path for the Charlicloud tarred image;

* `exec_env_conf`: specifiying all configuration related to the execution 
    environment.
  * a. `bee_charlicloud`: {}

##### Step 2. Launch task
* a. Prepare run scripts and beefile. See examples/bee-charliecloud-examples.

* b. Open `2` console windows. One serves as `Daemon Control`, another serves 
     as `Client Control`.

* c. On the `Daemon Control` window:
  * 1. Make your allocation.
  * 2. Load charliecloud and openmpi modules. For flecsale or lammps examples source the env... file.
  * 3. cd into a directory where you wish to send output.
  * 4. Run `bee_orc_ctl.py` to start the Bee Orchestration daemon. 

* c. On the `Client Control` window:
  * 1. ssh to allocated node (same as on the `Daemon Control` window.
  * 2. cd into a directory where you wish to send output.
  * 3. Load charliecloud and openmpi modules. 
       (For flecsale or lammps examples, source the env... file.)
  * 4. Run `bee_launcher.py`  to launch Bee job. 
       (i.e. bee_launcher.py -l task (task.beefile defines the job you just launched.)

      Options to launch, control, and monitor tasks.  
     `-l <task_name>`: runs task specified by <task_name>.beefile 
                       in the current directory;

     `-s`: list all tasks with status, automatically updates status;

     `-t <task_name>`: terminate task <task_name>;

     `-d <task_name>`: terminate and delete task <task_name> from task list;

     `-e <efs_name>`: create new efs with name <efs_name>.
   

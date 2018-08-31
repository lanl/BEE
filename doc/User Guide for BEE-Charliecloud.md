## Build and Execute Environment (BEE) User Guide for `BEE-Charliecloud`

The following guide shows you how to run `BEE-Charliecloud` on HPC environment.
Note that in order to utilize `BEE-Charliecloud` you will need to be in a `Slurm` environment and have access to [Charliecloud](https://github.com/hpc/charliecloud/). Additionally some aspects of 

### Installation
##### Step 1. Install dependencies
If this is your first time using BEE, run `install.sh`.

##### Step 2. Add bee launcher to $PATH
Add the directory of bee-launcher to $PATH, so that it can run anywhere.
`$ export PATH=<path_to_git_location>/BEE_Private/bee-launcher:$PATH`

##### Step 3. Verify additional requirements are satisfied
- Bash
- [Charliecloud](https://github.com/hpc/charliecloud)
- Slurm  

### Launch BEE-Charliecloud task

##### Step 1. Configure task (beefile) file (see examples/bee-charliecloud-examples)
Configure `<task_name>.beefile` file as follow:

* `task_conf`: specifiying configurations related to the task.
   * a. `task_name`: name of task to be executed; should be unique
         and the same as the beefile;

   * b. `exec_target`: `bee-charliecloud`;

   * c. `batch_mode`: `true` or `false`; For details, 
            refer to `User Guide for Batch Mode`.
            NOTE: As of the current release this is unsupported by the Charliecloud launcher

   * d. `general_run`: list of scripts that will be invoked on the head-node in the allocation after launching;
     * 1. `script`: name of the script. The script file needs to be in current
            directory.
     * 2. `flags`: A set of key/value pairs that equate to options for the `general_run` command. Anything provided via this method is not verified and you are responsible for ensuring the accuracy of these options. For example, the below values would would be seen as: `sh myscripts -ex 8 customValue ...`. Make note of the use of `null` if you are utilizing long names/value in a single key.
      ```json
      "flags": {
        "-ex": "8",
        "customValue": null
      }
      ```

   * e. `mpi_run`: list of scripts that will be run in parallel by MPI after 
         launching;
     * 1. `script`: name of the script. The script file needs to be in current
            directory.
     * 2. `node_list`: node names i.e. ["cn30", "cn31" ...] to run target job on;
     * 3. `map_by`: (optional)
            map_by flag for mpirun command i.e. "node" or "core", invalid if 
            no map_num
     * 4. `map_num`: argument to map_by flag.
     * 5. `flags`: A set of key/value pairs that equate to options for the `mpirun` command. Anything provided via this method is not verified and you are responsible for ensuring the accuracy of these options. For example, the below values would would be seen as: `mpirun -np 8 --quite ...`. Make note of the use of `null` if you are utilizing long names/value in a single key.
      ```json
      "flags": {
        "-np": "8",
        "--quite": null
      }
      ```
   * f. `srun_run`: list of scripts that will be run via `srun` across all nodes specified via `node_list` under  `exec_env_conf`. This is beneficial when utlizing the `BeeFlow` functionality within a single allocation.
     * 1. `flags`: A set of key/value pairs that equate to options for the `srun` command. Anything provided via this method is not verified and you are responsible for ensuring the accuracy of these options. For example, the below values would would be seen as: `srun -n 8 --mpi=pmi2 ...`. Make note of the use of `null` if you are utilizing long names/value in a single key.
      ```json
      "flags": {
        "-n": "8",
        "--mpi=pmi2": null
      }
      ```

* `container_conf`: Charliecloud container info.
  * a. `container_path`: entire path for the Charlicloud tarred image;
  * b. `remove_after_exec`: Upon the completion of the task remove the directory created via 'ch-tar2dir' (default value is false)
  * c. `container_tar2dir`: Directory the container (defined via `container_path`) is extracted to. Default location is `/var/tmp`

* `exec_env_conf`: specifying all configuration related to the execution 
    environment.
  * a. `bee_charlicloud`: {
     * 1. `node_list`: nodes i.e. ["cn30", "cn31" ...] to be utilized, this list specifies which nodes should be utilized as part of task. Insure that it is utlized to avoid potential conflicts and wasted resources when utlizing BeeFlow.
     
     Note: It is possible to not include `node_list` and BEE will use your entire allocation. For example, if the key is not found BEE will simply run all commands across the entire allocation, this means that the Charliecloud unpack step (`ch-tar2dir ...`) or any `srun_run` scripts will occurs on each node. This may lead to undesirable affects when the task is part of a workflow.
  }

##### Step 2. Launch task
* a. Prepare run scripts and beefile. See examples/bee-charliecloud-examples.

* b. Open `2` console windows. One serves as `Daemon Control`, another serves 
     as `Client Control`.

* c. On the `Daemon Control` window:
  * 1. Make your allocation.
  * 2. Load charliecloud and openmpi modules. 
         (For flecsale or lammps examples source the env... file.)
  * 3. cd to a directory where you wish to send output.
  * 4. Run `bee_orc_ctl.py` to start the Bee Orchestration daemon. 

* c. On the `Client Control` window:
  * 1. ssh to the same node as on the `Daemon Control` window.
  * 2. cd to the directory containing beefile and scripts. 
  * 3. Run `bee_launcher.py`  to launch Bee job. 
       (i.e. bee_launcher.py -l task (task.beefile defines the job to launch.)
       ** Note: If you get the message "Failed to locate nameserver":
          Make sure:
          1.  You are on the same nodes in both windows.
          2.  That bee_orc_ctl.py is running in the `Daemon Control` window.
 
      Options to launch, control, and monitor tasks.  
     `-l <task_name>`: unpacks Charliecloud image on /var/tmp then 
                       runs task specified by <task_name>.beefile 
                       in the current directory;

     `-s`: list all tasks with status, automatically updates status;

### Additional Notes
Support for `BeeFlow` has been added for the `Bee-Charliecloud` launcher. Please refer to the [documentation](https://github.com/lanl/BEE_Private/blob/master/doc/User%20Guide%20for%20BeeFlow.md) for details on how to create a workflow.

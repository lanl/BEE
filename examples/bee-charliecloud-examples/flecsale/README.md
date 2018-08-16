## Flecsale via BEE-Charliecloud
These examples demonstrate a number of ways to run Flecsale via the `BEE-Charliecloud` launcher. Either via a genral (`gen`) run targeting a single user defined scripts, `srun` utizling the Slurm command and custom flags, and finally `mpi`.

* These examples have been tested with Slurm 17.x and Charliecloud 0.9+

In order to run these examples you will need to have BEE properly installed and on the `BEE_Priave/bee-launcher/` folder defined on your systems `$PATH`.
Addtionally, please verify that the [proper container](https://hub.docker.com/r/beelanl/flecsale/) has been downloaded and Charliecloud (`ch-docker2tar`) run on the image. 

#### Step 1. 
Review the apprpirate `*.beefile` and insure that:
* `"container_path": "..."': Is pointing to the correct location of the Flecsale Charliecloud container.
* `"node_list": ["??", "??"]"`: Any instalce of `node_list` have been properly updated.

#### Step 2.
Log into your target system, you can either open two seperate terminals or work within a single terminal and utilize `screen` as opposed to `Window 1`.

#### Step 3. - On Window 1 
* `$ salloc -p <partition> -N <number of nodes>`
* `$ source env_cc_ompi_2.1.2` # loads charliecloud and openmpi (this is just an example for a particular cluster)jj
* `$ bee_orc_ctl.py` 

##### Step 4. - On Window 2
* Connect to node allocation in step 3
* `cd` to the example directory
* `$ bee_launcher.py -l flecsale_gen` # Alternatively you can speicifcy any other `.beefile`

This is will begin running the task defined via the `.beefile`, including unpacking the container and iniating the scripts that have been defined. Any console output during this process will appear on `Window 1`.

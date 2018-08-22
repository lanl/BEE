## LAMMPS via Charliecloud
### Requirements
	* BEE
	* Charliecloud
	* OpenMPI (1.10.7)
	* lammps_example.tar.gz file
		NOTE: Download via https://hub.docker.com/r/beelanl/cc-lammps/ and run `ch-tar2dir`

### General - Example
1. Open 2 terminals, `Daemon Control` and `Client Contol`
   * Alternatively you may run the `Daemon Control` via `screen`
2. Via `Daemon Control` terminal
 * 2.1. `$ salloc -p <partitionName>`
 * 2.2. CD to example directory
 * 2.3. Verify `lammps_cc_gen.beefile` properties
      * `"container_path": "..."`: Is pointing to the correct location of the Flecsale Charliecloud container.
      * `"node_list": ["??", "??"]"`: Any instance of `node_list` have been properly updated.
 * 2.4. `$ source env_cc_ompi1.10` # sets up environment (This is just and example for a particular cluster.)
 * 2.5. `$ bee_orc_ctl.py`
 * 2.6. Leave terminal open
3. Via `Client Control` terminal
 * 3.1. `ssh <node>` from `Daemon Control`
 * 3.2. CD to example directory
 * 3.3. `$ bee_launcher.py -l lammps_cc_gen`
4. Observe process either via `Daemon Control` and/or `$ bee_launcher.py -s`

### MPI - Example
1. Open 2 terminals, `Daemon Control` and `Client Control`
2. Via `Daemon Control` terminal
 * 2.1. `$ salloc -p <partitionName> -N3`
 * 2.2. CD to example directory
 * 2.3. Verify `lammps_cc_mpi.beefile` properties, care any referenced `nodes`
 * 2.4. `$ source env_cc_ompi1.10` # sets up environment (This is just and example for a particular cluster.)
 * 2.5. `$ bee_orc_ctl.py`
 * 2.6 Leave terminal open
3. Via `Client Control` terminal
 *	3.1. `ssh <node>' form 'Daemon Control`
 *	3.2. CD to example directory
 *	3.3. `$ bee_launcher.py -l lammps_cc_mpi`
4. Observe process either via `Daemon Control` and/or `$ bee_launcher.py -s`

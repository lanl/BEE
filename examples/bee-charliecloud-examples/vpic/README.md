## VPIC via Charliecloud
### Requirements
	* BEE
	* Charliecloud
	* OpenMPI (1.10.7)
	* vpic.tar.gz file
		NOTE: Build via `docker build -t vpic .` and `ch-docker2tar` using Charlicloud 
#### Container Notes    
Container utilized: https://github.com/j-ogas/charliecloud-examples/tree/1e6bb08d5db4c84c4a3ad7e58f5d1d331a3cc8f3/vpic
    
### General - Example
1. Open 2 terminals, `Daemon Control` and `Client Contol`
   * Alternatively you may run the `Daemon Control` via `screen`
2. Via `Daemon Control` terminal
 * 2.1. `$ salloc -p <partitionName>`
 * 2.2. CD to example directory
 * 2.3. Verify `vpic.beefile` properties
      * `"container_path": "..."`: Is pointing to the correct location of the Flecsale Charliecloud container.
      * `"node_list": ["??", "??"]"`: Any instance of `node_list` have been properly updated.
 * 2.4. `$ source env_cc_ompi1.10` # sets up environment (This is just and example for a particular cluster.)
 * 2.5. `$ bee_orc_ctl.py`
 * 2.6. Leave terminal open
3. Via `Client Control` terminal
 * 3.1. `ssh <node>` from `Daemon Control`
 * 3.2. CD to example directory
 * 3.3. `$ bee_launcher.py -l vpic`
4. Observe process either via `Daemon Control` and/or `$ bee_launcher.py -s`

0.1.0
    Initial Release of hpc-beeflow published on PYPI

0.1.3
    BEE now accepts stdout and stderr CWL specifications to direct those outputs for each task.

0.1.4
What's Changed
 - Scheduler options added for time-limit, account and partitions as CWL extensions
 - Fixes for MPI
 - Jinja file no longer required
 - Merge submit and start commands
 - Improved usability of 'beecfg new'
 - Combined gdbs
 - Add restart code to beeflow
 - Checkpoint restart fix
 - Allow Absolute/Relative Paths for Main CWL and YAML Files
 - Minimum version of Charliecloud required is now 0.32

0.1.5
- Combined beeflow, beeclient and beecfg commands. All commands now are invoked via beeflow.
- Fixed an obscure dependency issue between tasks
- Simplified config file, deleted duplications of bee_workdir
- CWL Parser was moved to the client
  - CwlParser is now instantiated in bee_client.py
  - CwlParser no longer invokes Workflow Interface, now returns Workflow and Task objects
  - Allows verification of CWL specification without running the workflow
- Added support for Flux scheduler

0.1.6
Clean up of processes, logs, and directory space
- Eliminates extraneous Neo4j instances from cancelled/failed tasks
- Cleans up log entries for query
- Improves start time for celery
- Makes start time configurable
- Decreases the number of celery processes
- Fixes capability to specify a main cwl file and/or yaml file not in the CWL directory
- Parses CWL after packaging the directory
- Moves temporary files for unit tests out of $HOME

0.1.7

Major features: adds the capability to include post- and pre-processing scripts to tasks, fixes the Checkpoint/Restart capability, increases logging, and adds some features to the client.
- Initial task manager resiliency and error handling (#789)
- Add pre/post script support (#788)
- Fix LOCALE error for systems where redis container failed to start
- Add logging to workflow interface (#764)
     - Enable logging in neo4j_cypher.py, neo4j_driver.py, and gdb_driver.py
- Add ``beeflow remove`` command to client
     - Enables removal of archived or cancelled workflows and associated artifacts
- Update minimum Charliecloud version to 0.36
- CI refactor to allow running jobs on runners other than github
- Add sumbit command options to workflow artifact for archive purposes 
- Increase maximum version of python to 3.12
- Fix Checkpoint/Restart capability
- Add testing for Checkpoint/Restart 
- Adds capability to reset the beeflow files (deletes all artifacts) especially useful for developers.

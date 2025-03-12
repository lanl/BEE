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

0.1.8

Features: Fixes sphinx version to enable publishing documentation, now includes
          CI for testing documentation builds

- Update sphinx version, update actions and release docs (#812)
- Add separate action for testing docs
- Fix beeflow config new error

0.1.9

Major features include:
   Changing graph database to use one instance of Neo4j
   Initial python api for generating CWL specification
   Added Rest API for beeflow
   Add ability to export graph of workflow and task states at any stage

- Updates the Graph Database to use one instance of Neo4j for all workflows for a user vs. using one for each workflow.  - impacts system resources
- Adds Python API for generating cwl specification of a workflow.
- Adds coverage metrics for unit tests. - improves reliability
- Adds resiliency to Task Manager (TM) now updates task states upon automatic restart of TM - improves resilience
- Enhances pre/post-script capabilities - added flux capability & checks for shell compatibility. - adds flexibility to each task
- Adds capability to export dag of a workflow before, during and after execution - enhancement verifing workflows prior to submit and visualizing state during run
- Adds Beeflow connect – A Rest API for BEEflow – capability to start a workflow from Continuous Integration (CI) tests (or on another system by user)

0.1.10

Major features include:

   Adding the capability to limit the number of jobs in active scheduling
   Improves archiving failed and cancelled workflows
   Improvements to API for generating CWL specifications
   Adds SlurmRequirements for qos and reservation
   Improved configuration
   Checks if beeflow is running on another front-end


 - Implement Archived/Partial-Fail workflow end state
 - Add --remote flag to beeflow core start (#1015)
 - Task failure only fails dependent tasks
 - Prevent multi-failed tasks archiving
 - Add job_limits to config; limit the number jobs in the job queue (#1010)
 - Prevent archiving if workflow is already archived
 - Set up unique remote port number as the default (#1007)
 - Adds regression test for archive_workflow in wf_update (#997)
 - Generate CWL Refactor (#1004)
 - Change SchedulerRequirement to SlurmRequirement; add qos and reservatio
 - Add CWL requirement beeflow:useContainer support for SquashFS (#990)
 - Add `pytest` tips to Developer's Guide (#999)
 - Corrects neo4j cypher queries that trigger warnings (#993)
 - Issue963/Make beeflow config new non-interactive by default (#983)
 - Remove extra messages about the openapi_version (#985)
 - Fix backend issues and reset client db (#981)
 - Issue979/Remove metadata command (#982)
 - Correct archives location (#973)
 - Issue877/Add config option for archive directory (#965)
 - Fix slurmrestd version function (#953)
 - Upgrade acceptable versions of python to <= 3.13.0 (#961)
 - Fix Cancel Workflows (#960)
 - Issue943/pull deps neo4j (#945)
 - Update requests-unixsocket to requests-unixsocket2 (#958)
 - Bump werkzeug from 3.0.4 to 3.0.6 (#952)
 - remove gdb ports from config (#940)
 - Archive Cancelled Workflows (#939)
 - Issue883/add check for different front end (#933)
 - Fix config issue and revise slurmrestd inference (#950)
 - Add flag to allow beeflow to run on back end node (#947)


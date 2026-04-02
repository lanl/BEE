### 0.1.11

Major features include:

New graph database SQLite implementation (now default) and support for Redis in Spack:
  - increased responsiveness and speed for managing workflows
  - eliminates requirement for dependent containers (Redis must be in the user's spack environment and SQLite must be specified as the graph database.)

Extends the capabilities of checkpointing/restarting including:
 - Support for additional parameters when restarting
 - Support for sentinel file to indicate needed restart
 - Support for restart when job is successful

CWL support:
  - Can specify a signal to be sent to slurm jobs
  - Can specify a file to load Slurm and MPI requirements from
  - Can specify a unique working directory for a task

Allows user to pause, resume, cancel or remove multiple (or all) workflows with one command, e.g. "beeflow pause --all".

Improvements were made for beeflow task information (now in a subdirectory), including batch script, metadata, outputs, and errors.

Code improvements and organization were made using Pydantic for object models.

An example AI/ML fire workflow has been included.

Dependent tasks now fail if the parent task has build failures, is cancelled, or times out (unless checkpoint/restarting is specified).

New attributes can be listed when querying workflow status.

Change log:

 -  Add more data artifacts when CI fails (#1176)
 -  Add signal to SlurmRequirement(#1186)
 -  Change default attributes (#1182)
 -  Bump pyasn1 from 0.6.2 to 0.6.3 (#1183)
 -  Fix GitHub actions for sqlite3 (#1180) (#1181)
 -  Update core.py for when slurmrestd isn't available. (#1179)
 -  Start 0.1.11dev6 after pre-release (#1177)
 -  (tag: 0.1.11dev5) Pre-release 0.1.11dev5 (#1175)
 -  Fix Slurmrestd Version Inference (#1168) (#1172)
 -  Implement Graph Database in SQLITE (#1155)
 -  Bump protobuf from 5.28.3 to 7.34.0rc1 (#1173)
 -  Bump pyasn1 from 0.6.1 to 0.6.2 (#1170)
 -  Bump urllib3 from 2.6.0 to 2.6.3 (#1169)
 -  Fix Slurm attribute errors when switching between schedulers and choosing new attributes (#1167)
 -  1092 posixpath task workdirs (#1148)
 -  Support for spack installed redis-server instead of containerized version (#1157)
 -  1152 Checkpoint/Restart when job does not fail but still needs a restart (#1160)
 -  Enable Slurm and MPI Requirement loading from file  for Inputs (#1144)
 -  Bump urllib3 from 2.2.3 to 2.6.0 (#1156)
 -  Impact multiple workflows with the same command  (#1146)
 -  Issue #1045 beeflow list output columns lineup (#1147)
 -  Remove container_path from Checkpoint Requirements, not used (#1153)
 -  (test-ci) use user provided wf name instead of cwl file name (#1150)
 -  Bump h11 from 0.14.0 to 0.16.0 (#1145)
 -  Fix networkx issue when numpy is also installed (#1142)
 -  Wf status refactoring (#1105)
 -  Use Pydantic for Object Models (#1091)
 -  Update documentation for pre-release 0.1.11dev4 (#1138)
 -  Start pre-release 0.1.11dev5 (#1137)
 -  (tag: 0.1.11dev4) Dump CWL and YAML as strings (#1122)
 -  Issue#1069 document warning overwrite checkpointed outputs (#1134)
 -  Provide more information when using 'beeflow query' for Flux (#1129)
 -  Create subdirectories for task scripts, outputs, and errors (#1128)
 -  Add fire workflow (#1120)
 -  Pypi site and logos (#1126)
 -  Start 0.1.11dev4 (#1125)
 -  (tag: 0.1.11dev3) Build pre-release documentation
 -  Add action to build documentation for pre-release tags
 -  (tag: 0d) Update pre-release version to 0.11.dev3 for publishing on PyPi (#1121)
 -  Make the default value of glob an empty string to it can always be joined with a directory. (#1119)
 -  Add Proper Wait Monitoring for Neo4j Being Up (#1098)
 -  Disable builder when no DockerRequirement present (#1057)
 -  Issue1081/check graphviz avail (#1083)
 -  Change version for pre-release 0.1.11dev2 (#1084)
 -  Create subdirectories for task scripts, outputs, and errors #1060 (#1077)
 -  Adds CWL option to change working directory for task (#1074)
 -  Relax pylint version (#1080)
 -  Add additional testing of `bee_client` (#1063)
 -  Support additional parameters when restarting (#1072)
 -  Modifies developer guide for poetry installation using a python environment (#1075)
 -  Fix blank restart_parameters shows None (#1070)
 -  Change restart name convention to name-1, name-2, etc (#1071)
 -  Adding tests to improve `bee_client` coverage (#1062)
 -  Add CheckpointRequirement to Python CWL API (#1059)
 -  Add some basic regression testing for `beeflow/common/cwl` (#1054)
 -  (origin/spack-develop) Start pre-release 0.1.11.dev1 (#1056)
 -  Fix CWL API and Move stdout/stderr (#1052)
 -  Fail dependent tasks for CANCELLED tasks (#1051)
 -  Combine unit test and integration test coverage (#1042)
 -  Fail dependent tasks for TIMEOUT (#1036)
 -  Add remote cli commands including connection, core-status, droppoint, copy, and submit.
 -  BUILD_FAIL should cause DEP_FAIL for dependent tasks (#1033)

### 0.1.10

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

### 0.1.9

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

### 0.1.8

Features: Fixes sphinx version to enable publishing documentation, now includes
          CI for testing documentation builds

- Update sphinx version, update actions and release docs (#812)
- Add separate action for testing docs
- Fix beeflow config new error

### 0.1.7

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

### 0.1.6
Clean up of processes, logs, and directory space
- Eliminates extraneous Neo4j instances from cancelled/failed tasks
- Cleans up log entries for query
- Improves start time for celery
- Makes start time configurable
- Decreases the number of celery processes
- Fixes capability to specify a main cwl file and/or yaml file not in the CWL directory
- Parses CWL after packaging the directory
- Moves temporary files for unit tests out of $HOME

### 0.1.5
- Combined beeflow, beeclient and beecfg commands. All commands now are invoked via beeflow.
- Fixed an obscure dependency issue between tasks
- Simplified config file, deleted duplications of bee_workdir
- CWL Parser was moved to the client
  - CwlParser is now instantiated in bee_client.py
  - CwlParser no longer invokes Workflow Interface, now returns Workflow and Task objects
  - Allows verification of CWL specification without running the workflow
- Added support for Flux scheduler

### 0.1.4
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

### 0.1.3
    BEE now accepts stdout and stderr CWL specifications to direct those outputs for each task.

### 0.1.0
    Initial Release of hpc-beeflow published on PYPI



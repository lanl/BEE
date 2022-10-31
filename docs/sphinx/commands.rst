Commands
************

There are two main commands that you should be familiar with to use BEE. Those are "beeflow" and "bee_client". Each of these have sub-commands to do various things with the client or daemon. 


beeflow
============

beeflow is the command you will use to interact with the daemon process. The following are the options:

"beeflow start": Attempt to daemonize if not in debug and start all BEE components.

Options:
  -F, --foreground  run in the foreground  [default: False]


"beeflow status": Check the status of beeflow and the components.

"beeflow stop": Stop the current running beeflow daemon.

"beeflow --version": Display the version number of BEE.

bee_client
===========

bee_client is the command you will use to submit jobs and interact with your jobs. The following are the options:

"bee_client submit": Submit a new workflow.

Arguments:
  - WF_NAME, The workflow name  [required]
  - WF_PATH, Path to the workflow tarball  [required]
  - MAIN_CWL, filename of main CWL file  [required]
  - YAML, filename of YAML file  [required]
  - WORKDIR, working directory for workflow containing input + output files [required]
  
"bee_client start": Start a workflow with a workflow ID.

Arguments:
  - WF_ID  [required]
  
"bee_client package": Package a workflow into a tarball.

Arguments:
  - WF_PATH,       Path to the workflow package directory  [required]
  - PACKAGE_DEST,  Path for where the packaged workflow should be saved [required]
  
"bee_client listall": List all workflows

"bee_client query": Get the status of a workflow.

Arguments:
  - WF_ID  [required]
  
"bee_client pause": Pause a workflow (Running tasks will finish)

Arguments:
  WF_ID  [required]
  
"bee_client resume": Resume a paused workflow.

Arguments:
  WF_ID  [required]

"bee_client cancel": Cancel a workflow.

Arguments:
  WF_ID  [required]
  
"bee_client copy": Copy an archived workflow.

Arguments:
  WF_ID  [required]
  
"bee_client reexecute": Reexecute an archived workflow.

Arguments:
  WF_ID  [required]



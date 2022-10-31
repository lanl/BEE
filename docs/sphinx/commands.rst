Commands
************

There are two main commands that you should be familiar with to use BEE. Those are "beeflow" and "beeclient". Each of these have sub-commands to do various things with the client or daemon. 


beeflow
============

beeflow is the command you will use to interact with the daemon process. The following are the options:

``beeflow start``: Attempt to daemonize (if not in debug) and start all BEE components.

Options:
  -F, --foreground  run in the foreground  [default: False]


``beeflow status``: Check the status of beeflow and the components.

``beeflow stop``: Stop the current running beeflow daemon.

``beeflow --version``: Display the version number of BEE.

beeclient
===========

beeclient is the command you will use to submit jobs and interact with your jobs. The following are the options:

``beeclient submit``: Submit a new workflow.

Arguments:
  - WF_NAME, The workflow name  [required]
  - WF_PATH, Path to the workflow tarball  [required]
  - MAIN_CWL, filename of main CWL file  [required]
  - YAML, filename of YAML file  [required]
  - WORKDIR, working directory for workflow containing input + output files [required]

``beeclient start``: Start a workflow with a workflow ID.

Arguments:
  - WF_ID  [required]

``beeclient package``: Package a workflow into a tarball.

Arguments:
  - WF_PATH,       Path to the workflow package directory  [required]
  - PACKAGE_DEST,  Path for where the packaged workflow should be saved [required]

``beeclient listall``: List all workflows

``beeclient query``: Get the status of a workflow.

Arguments:
  - WF_ID  [required]

``beeclient pause``: Pause a workflow (Running tasks will finish)

Arguments:
  WF_ID  [required]

``beeclient resume``: Resume a paused workflow.

Arguments:
  WF_ID  [required]

``beeclient cancel``: Cancel a workflow.

Arguments:
  WF_ID  [required]

``beeclient copy``: Copy an archived workflow.

Arguments:
  WF_ID  [required]

``beeclient reexecute``: Reexecute an archived workflow.

Arguments:
  WF_ID  [required]



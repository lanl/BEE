Command Line Interface
**********************

BEE is controlled by one "**beeflow**" command with sub-commands to do various operations with the client or daemon.

BEE Daemon
============

To interact with the daemon process you'll need to use the ``beeflow core`` sub-command. The following are the options:

``beeflow core start``: Daemonize (if not in debug) and start all BEE components.

Options:
  -F, --foreground  run in the foreground  [default: False]


``beeflow core status``: Check the status of beeflow and the components.

``beeflow core stop``: Stop the current running beeflow daemon.

``beeflow core --version``: Display the version number of BEE.

``beeflow core reset``: Stop the beeflow daemon and cleanup the .beeflow directory to start from a fresh install. 

Arguments:
    - ``--archive``, ``-a``, Save a copy of the current .beeflow directory before removal. [optional]

Submission and workflow commands
================================

This section shows what commands you can use to submit and interact with your workflows. The following are the major options:

``beeflow submit``: Submit a new workflow. By default this will also start
jobs immediately (unless passed the ``--no-start`` option). If either the MAIN_CWL or YAML
files are not contained immediately inside of WF_PATH, then the WF_PATH directory will
be copied into a temporary directory and the missing files will then be copied
into the copied WF_PATH directory before packaging and submission.

Arguments:
  - WF_NAME, The workflow name  [required]
  - WF_PATH, Path to the workflow CWL tarball or directory  [required]
  - MAIN_CWL, filename of main CWL file  [required]
  - YAML, filename of YAML file  [required]
  - WORKDIR, working directory for workflow containing input + output files [required]
  - ``--no-start``, don't start the workflow immediately

``beeflow start``: Start a workflow with a workflow ID. Only needed if
``beeflow submit`` was passed the ``--no-start`` option.

Arguments:
  - WF_ID  [required]

``beeflow package``: Package a workflow into a tarball.

Arguments:
  - WF_PATH,       Path to the workflow package directory  [required]
  - PACKAGE_DEST,  Path for where the packaged workflow should be saved [required]

``beeflow list``: List all workflows

``beeflow query``: Get the status of a workflow.

Arguments:
  - WF_ID  [required]

``beeflow pause``: Pause a workflow (Running tasks will finish)

Arguments:
  WF_ID  [required]

``beeflow resume``: Resume a paused workflow.

Arguments:
  WF_ID  [required]

``beeflow cancel``: Cancel a workflow.

Arguments:
  WF_ID  [required]

``beeflow copy``: Copy an archived workflow.

Arguments:
  WF_ID  [required]

``beeflow reexecute``: Reexecute an archived workflow.

Arguments:
  WF_ID  [required]

Generating and Managing Configuration Files
===========================================

You can use the ``beeflow config`` sub-command to configure BEE for your workflows. The following are further options for this sub-command:

``beeflow config validate``: Validate an existing configuration file.

``beeflow config info``: Display some info about bee.conf's various options.

``beeflow config new``: Create a new config file.

``beeflow config show``: Show the contents of current bee.conf.




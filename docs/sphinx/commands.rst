.. _command-line-interface:

Command Line Interface
**********************

BEE is controlled by one "**beeflow**" command with sub-commands to do various operations with the client or daemon.

BEE Daemon
============

To interact with the daemon process you'll need to use the ``beeflow core`` sub-command. The following are the options:

``beeflow core start``: Daemonize (if not in debug) and start all BEE components.

Options:
  -F, --foreground  run in the foreground  [default: False]
  -B, --backend  run on a back end node  [default: False]
  -R, --remote  allow remote interactions  [default: False]

``beeflow core status``: Check the status of beeflow and the components.

``beeflow core info``: Get information about beeflow, including .beeflow directory location, log location, and version number.

``beeflow core stop``: Stop running beeflow components. Active workflows will be paused. You may continue running paused workflows with the ``beeflow resume <wf_id>`` command. Once you start beeflow components after a stop, you should check the status of workflows, query any running workflows. If they were intializing when a ``beeflow core stop`` was issued, the workflow may be running with tasks stuck in the waiting state. If this occurs and you want the workflow to continue pause and resume the workflow (``beeflow pause <wf_id>``, ``beeflow resume <wf_id>``) or to start over cancel the workflow (``beeflow cancel <wf_id>``) and resubmit it.

``beeflow core --version``: Display the version number of BEE.

``beeflow core reset``: Stop the beeflow daemon and cleanup the bee_workdir directory to start from a fresh install.

Options:
   ``--archive``, ``-a``, Backup logs, workflows, and containers in bee_workdir directory before removal. [optional]

``beeflow core pull-deps``: Pull and build BEE dependency containers. A new bee configuration file will be automatically generated with the new dependency container locations.

Options:
   ``--outdir``, ``-o``,


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
  - MAIN_CWL, filename of main CWL (if using CWL tarball), path of main CWL (if using CWL directory) [required]
  - YAML, filename of yaml file (if using CWL tarball), path of yaml file (if using CWL directory) [required]
  - WORKDIR, working directory for workflow containing input + output files [required]
  - ``--no-start``, don't start the workflow immediately

``beeflow start``: Start a workflow with a workflow ID. Only needed if
``beeflow submit`` was passed the ``--no-start`` option.

Arguments:
  - WF_ID  [required]

``beeflow package``: Package a workflow into a tarball.

Arguments:
  - WF_PATH       Path to the workflow package directory  [required]
  - PACKAGE_DEST  Path for where the packaged workflow should be saved [required]


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

``beeflow remove``: Remove cancelled or archived workflow and it's information.

Arguments:
  WF_ID  [required]

``beeflow copy``: Copy an archived workflow.

Arguments:
  WF_ID  [required]

``beeflow reexecute``: Reexecute an archived workflow.

Arguments:
  WF_ID  [required]

``beeflow dag``: Export a directed acyclic graph (DAG) of a submitted workflow. This command can be run at any point of the workflow. To see the DAG of a workflow before it runs, submit the workflow with the ``--no-start`` flag and then use the dag command. The DAGs are exported to $OUTPUT_DIR/$WD_ID-dags by default. If the ``no-dag-dir`` flag is specified when the dag command is run, the DAG will be exported to $OUTPUT_DIR. The dag command makes multiple versions of the DAGs. The most recent version is $WF_ID.png and the others are $WD_ID_v1.png, $WF_ID_v2.png ... where v1 is the oldest. See :ref:`workflow-visualization` for more information.

Arguments:
  - WF_ID  [required]
  - OUTPUT_DIR, Directory for the output  [required]
    
Options:
  ``no-dag-dir``: Do not make a subdirectory within the output_dir for the DAGs.

Generating and Managing Configuration Files
===========================================

You can use the ``beeflow config`` sub-command to configure BEE for your workflows. The following are further options for this sub-command:

``beeflow config validate``: Validate an existing configuration file.

``beeflow config info``: Display some info about bee.conf's various options.

``beeflow config new``: Create a new config file.

``beeflow config show``: Show the contents of current bee.conf.




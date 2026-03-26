Common Workflow Language (CWL)
******************************
BEE workflows are written in the Common Workflow Language (CWL). CWL allows
workflows to be written in a simple YAML format that can represent "steps" (or
tasks) of a workflow as well as how those steps depend on each other. Each step
has a base command to be used along with inputs and outputs. Special options
are used to indicate how those inputs and outputs can be used to form the
actual command to be run on a system. In addition, requirements and hints are
special options that determine what a particular step requires and the
environment in which the step can run. Dependencies are expressed naturally
through the inputs and outputs that flow between the tasks.

In the past each workflow orchestration system would use a different workflow
format, based on their needs at the time. Thus when someone would write a
workflow for one system, it would be time consuming to port that workflow over
to another system. This is one of the main reasons for creating the CWL_ standard
and today a number of workflow systems like BEE support it. By using this
standard we hope to make it easier on users to both write and extend their
workflows for different systems.

.. _CWL: https://www.commonwl.org/

BEE currently supports a subset of the CWL standard. On this page we'll try to
list any differences between the CWL standard and what BEE supports, as well as
extensions that you might want to use.

For general information about writing workflows please take a look at the
`Common Workflow Language User Guide`_. If you have more questions or are
interested in particular details of CWL, then you might want to take a look at
the specification_.

.. _Common Workflow Language User Guide: https://www.commonwl.org/user_guide/
.. _specification: https://www.commonwl.org/v1.2/

BEE-Specific Requirements/Hints
===============================

Requirements and hints are both used to help BEE configure the environment for
each step. When a requirement is encountered in a workflow the workflow system
must be able to fulfill it, or raise an error indicating a failure. On the
other hand if a hint is not supported, then it can safely be ignored by the
implementation. Since the standard only includes a limited number of
requirements, not all of which are useful for an HPC setting, we've added some
extensions that are prefixed with ``beeflow:``. Please specify beeflow extensions as hints in the steps of your CWL workflow specification.

DockerRequirement
-----------------

A ``DockerRequirement`` (a CWL standard specification) is used to run a step with a container. BEE does not
support Docker, but it does support Charliecloud_ and also has limited support
for Singularity_.

.. _Charliecloud: https://hpc.github.io/charliecloud/
.. _Singularity: https://apptainer.org/

An example ``DockerRequirement`` in BEE is shown below::

    DockerRequirement:
        dockerFile: "dockerfile-name"
        beeflow:containerName: "some-container"

This example includes two suboptions, a ``dockerFile`` option that specifies
the name of of a dockerfile as well as an extension ``beeflow:containerName``
that gives the name of the container to build. Below are some of the suboptions
that BEE supports and how they can affect running a step with a container.

.. |vspace| raw:: latex

   \vspace{5mm}

.. |br| raw:: html

   <br />


========================= =========================================================
Suboption Name            Usage/Meaning/Requirements
========================= =========================================================
``dockerPull``            ``dockerPull: "container-image"`` |vspace| |br|
                          Pull from a container repository.

``dockerLoad``            Not supported

``dockerFile``            ``dockerFile: "dockerfile-name"`` |vspace| |br|
                          Builds a container using the dockerfile. |vspace| |br|
                          Requires: ``beeflow:containerName``

``dockerImport``          Not supported
``dockerImageId``         Not supported
``dockerOutputDirectory`` Not supported

``beeflow:copyContainer`` ``beeflow:copyContainer: "path-to-container-image"`` |vspace| |br|
                          Copies image to ``container_archive`` (specified in bee.conf). Uses copy.

``beeflow:useContainer``  ``beeflow:useContainer: "path-to-container-image"`` |vspace| |br|
                          Executes using the specified image.

``beeflow:containerName`` ``beeflow:containerName: "containerName"`` |vspace| |br|
                          Specifies the container name. Used in conjunction with dockerFile.
``beeflow:forceType``     ``beeflow:forceType: "forceType"`` |vspace| |br|
                          Charliecloud specific option that |vspace| |br|
                          corresponds to ``ch-image``'s ``--force`` argument.
========================= =========================================================

beeflow:MPIRequirement
----------------------

BEE also includes a special requirement for running MPI jobs. Note that CWL has
also experimented with a cwltool specific hint (see their paper_). The
experimental extension includes basic support for running MPI jobs, but doesn't
include all of the options that are important for the HPC systems that BEE is
designed to run on. For instance, many jobs will require some sort of mpi
runtime information that needs to be passed to the underlying scheduler (such
as the mpi type that needs to be passed to Slurm with the ``--mpi={version}``
option).

.. _paper: https://ieeexplore.ieee.org/document/9308116

BEE's ``beeflow:MPIRequirement`` attempts to be as configurable as possible for
running HPC jobs with MPI. An example ``beeflow:MPIRequirement`` in BEE is
shown below::

    beeflow:MPIRequirement:
      nodes: 10
      ntasks: 32

The values for ``nodes`` and  ``ntasks`` are then passed to the template and
can be used to request the required resources from the underlying scheduler on
submission.

Alternately you can load the requirements from a json formatted text.
file and use the "load_from_file" option::

    beeflow:MPIRequirement:
      load_from_file: "mpi_conf.json"

Contents of mpi_conf.json::

   {
     "nodes": 10,
     "ntasks": 32
   }

beeflow:CheckpointRequirement
-----------------------------

BEE is designed to manage workflows that include long running scientific
simulations, requiring checkpointing and restarting. We implemented the
``beeflow:CheckpointRequirement`` for this purpose. If a step in a workflow
includes this requirement and the task stops, such as for a timelimit on the job,
a subtask will run to continue the simulation using the specified checkpoint
file.

Basic Checkpoint/Restart Example
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A basic example ``beeflow:CheckpointRequirement`` in BEE is shown below::

       beeflow:CheckpointRequirement:
            enabled: true
            checkpoint_dir: checkpoint_output
            file_regex: backup[0-9]*.crx
            restart_parameters: -R
            add_parameters: --additional-options True
            num_tries: 3

For the above example ``checkpoint_dir`` is the directory containing the
checkpoint files. The ``file_regex`` specifies the regular expression for the
possible checkpoint filenames. The ``restart_parameter`` will be added to the
run command followed by the path to the latest checkpoint file. ``add_parameters``
allows for additional parameters that need to be specified; these will be appended
to the run command after the checkpoint file. ``num_tries`` specifies the maximum
number of times the task will be restarted (default: 100, use ``null`` for unlimited).

Sentinel File-Based Restart
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

BEE also supports sentinel file-based checkpoint/restart logic, allowing tasks to
restart based on the presence or absence of a sentinel file. This is useful when
your application creates a file to indicate completion or when restart should be
triggered based on external conditions.

An example using sentinel file logic::

       beeflow:CheckpointRequirement:
            enabled: true
            checkpoint_dir: checkpoint_output
            file_regex: backup[0-9]*.crx
            restart_parameters: -R
            num_tries: 3
            sentinel_file_path: continue.file
            restart_on_file_exists: true
            restart_on_failure: false

CheckpointRequirement Parameters
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

========================== ===== =========================================================
Parameter                  Req   Description
========================== ===== =========================================================
``enabled``                Yes   Enable/disable checkpointing (true/false)

``file_regex``             Yes   Regular expression pattern matching checkpoint filenames

``restart_parameters``     Yes   CLI flag for restart (e.g., "-R") that precedes the
                                 checkpoint file path

``add_parameters``         No    Additional CLI parameters appended after checkpoint file

``num_tries``              No    Maximum restart attempts (default: 100)

``sentinel_file_path``     No    Path to sentinel file (relative to task working directory or absolute). |vspace| |br|
                                 When specified, restart logic checks this file's existence.

``restart_on_file_exists`` No    If ``true``: restart when sentinel file EXISTS  |vspace| |br|
                                 If ``false``: restart when sentinel file DOES NOT exist |vspace| |br|
                                 Only used when ``sentinel_file_path`` is specified

``restart_on_failure``     No    If ``true`` (default): only restart on FAILED/TIMEOUT |vspace| |br|
                                 If ``false``: also check sentinel for COMPLETED tasks |vspace| |br|
                                 Only used when ``sentinel_file_path`` is specified

``last_good_restart``      No    Path to store/reference the last good checkpoint |vspace| |br|
                                 (reserved for future use)
========================== ===== =========================================================

.. container:: red-block

   Warning: beeflow is not responsible for preserving outputs from each restart
   subtask. We suggest you include a pre-script to preserve any desired intermediate 
   outputs. To do this use `beflow:ScriptRequirement` and a script similar to 
   the examples below (shown for both tcsh and bash):

Example pre-script to preserve outputs during Checkpoint/Restarts (tcsh)
      -- Contributed by Lilikoi Latimer

.. code-block::

     # Cleanup output files from previous job
     # Make outputs folder if it doesn't already exist
     if (! -d outputs ) then
        mkdir outputs
     endif
     # Set list of file extensions to move
     set output_ext=(.example .extensions .here)

     # Prevents errors with setting array to patterns if no
     # files matching the pattern are found
     set nonomatch

     # Move output files
     foreach ext ($output_ext)
         set pattern="*$ext"
         set timestamp=`date "+%Y%m%d%H%M%S"`

         # Make list of files with extension, continuing if none exist
         set files=($pattern)
         if (! -e $files[1] ) then
             continue
         endif

         # Loop through files, moving to outputs
         foreach file ($files)
             cp $file "outputs/$file.$timestamp"
         end
     end

     unset nonomatch

Example pre-script to preserve outputs during Checkpoint/Restarts (bash)
      -- Contributed by Lilikoi Latimer

.. code-block::

     set -euo pipefail

     # Cleanup output files from previous job

     # Make outputs folder if it doesn't already exist
     mkdir -p outputs

     # Set list of file extensions to move
     output_ext=(.example .extensions .here)

     # Prevents treating unmatched globs as literals
     shopt -s nullglob

     # Move output files
     for ext in "${output_ext[@]}"; do
         pattern="*${ext}"
         timestamp=$(date "+%Y%m%d%H%M%S")

         # Make list of files with extension, continue if none exist
         files=($pattern)
         ((${#files[@]} == 0)) && continue

         # Loop through files, copying to outputs with timestamp
         for file in "${files[@]}"; do
             cp -- "$file" "outputs/$file.$timestamp"
         done
     done

     # Restore default globbing behavior
     shopt -u nullglob


beeflow:SlurmRequirement
----------------------------

This requirement is designed for specifying additional information that will be
passed to the Slurm scheduler during job submission. Each of the options can be 
set in the configuration file bee.conf under the ``job`` section to use for all
workflows. Setting any beeflow:SlurmRequirement in the CWL file will override the 
setting in bee.conf. Current options supported are:

* ``account`` - account name to run the job with (often used for charging).
* ``partition`` - partition to launch job on.
* ``qos`` - quality of service to use.
* ``signal`` - sends signal to batch shell or all job steps within slurm job
* ``reservation`` - reservation to use to launch job.
* ``timeLimit`` - time limit for the job in the format that Slurm uses currently.

Alternately you can add any of the above requirements to a json formatted text 
file and use the "load_from_file" option.

An example is shown below::

    beeflow:SlurmRequirement:
      timeLimit: 00:00:10
      account: account12345
      partition: partition-a
      signal: B:SIGUSR1@60
      qos: long
      reservation: reservation-a

Alternate::

    beeflow:SlurmRequirement:
       load_from_file: "slurm_conf.json"

Contensts of slurm_conf,json::

    {
     "timeLimit": "00:00:10",
     "account": "account12345",
     "partition": "partition-a",
     "signal": "B:SIGUSR1@60",
     "qos": "long",
     "reservation": "reservation-a"
    }


beeflow:ScriptRequirement
-------------------------

Some tasks may require small additional commands for setup or teardown such as
loading modules, setting up checkpointing files, perserving outputs of subtasks
that have been restarted, or cleaning up after a run.
The script requirement enables this by adding shell scripts that will run before
and after a task. The script must be within the workflow directory. The desired
shell interpreter must be specified in both the ``beeflow:ScriptRequirement`` section
of the cwl file as well as the shebang line of the script, otherwise, an error will be
returned. Furthermore, if different shell interpreters are specified, then expect
an error. Default shell environment variable is ``/bin/bash``. The pre_script is run 
before a task and the post_script is run after. Currently, we only support running 
scripts outside of a container. We are considering adding container support in the 
future.

ScriptRequirement currently supports the following options:

* ``enabled`` - Enables pre/post script support
* ``pre_script`` - Path to the pre_script relative to the workflow directory. 
* ``post_script`` - Path to the post_script relative to the workflow directory.
* ``shell`` - Desired shell interpreter. Must match shell interpreter defined in pre/post scripts.

An example ``beeflow:ScriptRequirement`` is shown below::

    beeflow:ScriptRequirement:
      enabled: True
      pre_script: before.sh
      post_script: after.sh
      shell: /bin/bash

beeflow:TaskRequirement
-------------------------

* ``workdir`` - Enables the use of a different working directory for a task

Example for using ``beeflow:TaskRequirement`` shown below::


    beeflow:TaskRequirement:
      workdir: ~/task_workdir

Notes:

1.) The task workdir can be an absolute path or relative to the workdir specified by the submit command.

2.) When using containers, the relative path is used. If a step depends on the output of a previous step, the task_workdir for the subsequent task must match, or you can use pre-script to place the required files in the proper subdirectory.

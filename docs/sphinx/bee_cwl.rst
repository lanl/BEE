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

beeflow:CheckpointRequirement
-----------------------------

BEE is designed to manage workflows that include long running scientific
simulations, requiring checkpointing and restarting. We implemented the
``beeflow:CheckpointRequirement`` for this purpose. If a step in a workflow
includes this requirement and the task stops, such as for a timelimit on the job, 
a subtask will run to continue the simulation using the specified checkpoint
file.

An example ``beeflow:CheckpointRequirement`` in BEE is shown below::

       beeflow:CheckpointRequirement:
            enabled: true
            file_path: checkpoint_output
            container_path: checkpoint_output
            file_regex: backup[0-9]*.crx
            restart_parameters: -R
            num_tries: 3

For the above example ``file_path`` is the location of the checkpoint_file. The
``file_regex`` specifies the regular expression for the possible checkpoint
filenames, the ``restart parameter`` will be added to the run command followed
by the path to the latest checkpoint file, and ``num_tries`` specifies the maximum
number of times the task will be restarted.

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
* ``reservation`` - reservation to use to launch job.
* ``timeLimit`` - time limit for the job in the format that Slurm uses currently.

An example is shown below::

    beeflow:SchedulerRequirement:
      timeLimit: 00:00:10
      account: account12345
      partition: partition-a
      qos: long
      reservation: reservation-a 

beeflow:ScriptRequirement
-------------------------

Some tasks may require small additional commands for setup or teardown such as
loading modules, setting up checkpointing files, or cleaning up after a run.
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

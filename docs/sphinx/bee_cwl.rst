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
running HPC jobs with MPI. Currently we use a special `Jinja file`_ that is
used as a template for generating submission scripts. All options in the
``beeflow:MPIRequirement`` get passed to the `Jinja file`_ template and can
then be used to make step-level decisions for running MPI jobs. Note that we're
also exploring other ways to implement this directly from the options within
the CWL files, instead of using a template file.

An example ``beeflow:MPIRequirement`` in BEE is shown below::

    beeflow:MPIRequirement:
      nodes: 10
      ntasks: 32

The values for ``nodes`` and  ``ntasks`` are then passed to the template and
can be used to request the required resources from the underlying scheduler on
submission.

See our section on the `Jinja file`_ for more info on how this works currently.

beeflow:CheckpointRequirement
-----------------------------

BEE is designed to manage workflows that include long running scientific
simulations, requiring checkpointing and restarting. We implemented the
``beeflow:CheckpointRequirement`` for this purpose. If a step in a workflow
includes this requirement and the task stops such as for a timelimit on the job
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
``file_regex`` specifies the regular expresion for the possible checkpoint
filenames, the ``restart parameter`` will be added to the run command followed
by the path to the checkpoint file, and ``num_tries`` specifies the maximum
number of times the task will be restarted.

.. _Jinja file:

Jinja File Templating
---------------------

When BEE launches a step of a workflow on an HPC system, the step and its
metadata are given as input to a special template file. The generated output is
used as the submission script for Slurm or LSF. While this allows a good deal
of flexibility for different types of HPC jobs, it also makes it difficult to
use. Currently, this section explains how it works and how you can configure
the template file for the needs of your workflow, but please note that we're
also exploring different ways to do this, so this functionality may change in
future releases.

These templates use the Jinja2_ templating library. While originally designed
for templating HTML, it can also be used for generating any text file. It also
has a simple Python-like syntax which should make it somewhat easy to work with
for those already familiar with the language.

.. _Jinja2: https://jinja.palletsprojects.com/en/3.1.x/

See the `Jinja Template Documentation`_ for more information on the templating
language and how to use it. There are also some example Jinja Files in
``beeflow/data/job_templates``.


.. _Jinja Template Documentation: https://jinja.palletsprojects.com/en/3.1.x/templates/

Here is a small example of a Jinja submit file for Slurm::

    #!/bin/bash
    #SBATCH --job-name={{task_name}}-{{task_id}}
    #SBATCH --output={{task_save_path}}/{{task_name}}-{{task_id}}.out
    #SBATCH --error={{task_save_path}}/{{task_name}}-{{task_id}}.err
    {% if 'beeflow:MPIRequirement' in hints and 'nodes' in hints['beeflow:MPIRequirement'] %}
    #SBATCH -N {{ hints['beeflow:MPIRequirement']['nodes'] }}
    {% endif %}
    {% if 'beeflow:MPIRequirement' in hints and 'ntasks' in hints['beeflow:MPIRequirement'] %}
    #SBATCH -n {{ hints['beeflow:MPIRequirement']['ntasks'] }}
    {% endif %}

    {{ env_code }}

    # pre commands
    {% for cmd in pre_commands %}
    srun {{ cmd|join(' ') }}
    {% endfor %}

    # main command
    srun {{ main_command|join(' ') }}

    # post commands
    {% for cmd in post_commands %}
    srun {{ cmd|join(' ') }}
    {% endfor %}

By default when you run ``bee_cfg new``, a default template file will be
generated for you, not unlike the one above.  The default template for Slurm
accepts the number of nodes and the number of tasks and submits corresponding
``#SBATCH`` directives for the job. You may also add other ``#SBATCH`` (or for
LSF ``#BSUB``) directives to your jinja file, to use particular partitions or
for accounting purposes.

This default template should work fine for most workflows, so you really don't
need to worry about editing it unless you need something extra. The important
parts to note above, are where the template code is generating the ``#SBATCH``
directives by checking the contents of the ``hints`` variable and the code
under the ``# main command`` comment which is where the command for a step will
be added. If you need to use a specific MPI type, then you may want to add
``--mpi={type}`` on the line under the ``main command`` comment. Or if you need
something extra from the scheduler, then you may want to add it to the
directives, or you can add the option on the main command itself.

If you only need to apply some particular option to one step of a workflow,
then you'll need to use Jinja's if_ construct to handle the case for that
particular step and then for the other steps. There are also some other
constructs, such as for_ loops, which may be useful for more complicated
workflows. The good thing is that most of these behave and act like normal
Python code, except being delimited by ``{% .. %}``.

.. _if: https://jinja.palletsprojects.com/en/3.1.x/templates/#if
.. _for: https://jinja.palletsprojects.com/en/3.1.x/templates/#for

Check the bee configuration file (bee.conf) or type ``bee_cfg show`` for the
current location of your job_template. If you need to, edit it for your
particular needs.

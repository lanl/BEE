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
extensions that are prefixed with ``beeflow:``.

DockerRequirement
-----------------

A ``DockerRequirement`` is used to run a step with a container. BEE doesn't
support Docker, but it does support Charliecloud_ and also has limited support
for Singularity_.

.. _Charliecloud: https://hpc.github.io/charliecloud/
.. _Singularity: https://apptainer.org/

An example ``DockerRequirement`` in BEE is the below::

    DockerRequirement:
        dockerFile: /some/path/to/source/Dockerfile
        beeflow:containerName: "some-container"

This includes two suboptions, a ``dockerFile`` option that points to a location
of a Dockerfile as well as an extension ``beeflow:containerName`` that gives the
name of the container to build. Below are some of the suboptions that BEE
supports and how they can affect running a step with a container.

========================= =========================================================
Suboption Name            Meaning/Usage
========================= =========================================================
``dockerPull``            Pull from a remote container repository. This would be in
                          the same format you would do with a
                          ``docker pull $container`` or a
                          ``ch-image pull $container``.
``dockerLoad``            Not supported
``dockerFile``            Takes a file path pointing to a ``Dockerfile`` to build
                          with the container runtime. This will be built just
                          before the step/task runs. Note that this also requires
                          ``beeflow:containerName`` to specify a name to use for
                          building.
``dockerImport``          Not supported
``dockerImageId``         Not supported
``dockerOutputDirectory`` Not supported
``beeflow:copyContainer`` This option takes the path of a Charliecloud tarball and
                          will copy this into your ``container_archive`` location
                          as specified in the bee.conf file.
``beeflow:useContainer``  This is similar to the ``beeflow:copyContainer`` option
                          above, but it does not copy the container into the
                          ``container_archive``.
``beeflow:containerName`` Give the name of a container to be used when building the
                          container for a step. This is only valid when also used
                          with the ``dockerFile`` option.
========================= =========================================================

beeflow:MPIRequirement
----------------------

...

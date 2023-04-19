.. _installation:

Installation Guide
******************

This section describes how to install BEE and requirements for installation.

Requirements:
=============

    * **Python version 3.8 (or greater)**

    * `Charliecloud <https://hpc.github.io/charliecloud/>`_ **version 0.27 (or greater)**
        Charliecloud is installed on Los Alamos National Laboratory (LANL) clusters and can be invoked using the `load module` command. Charliecloud is also easily installed in user space and requires no privilege to install. BEE runs dependencies from a Charliecloud container and uses Charliecloud to run the graph database neo4j and other dependencies. The default container runtime for containerized applications in BEE is Charliecloud.


    * **BEE dependency container**:
        If you are on a LANL system, you may use the dependency container supplied by the BEE team: **/usr/projects/BEE/neo4j-3-5-17-ch.tar.gz**

        At this time the only dependency needed in a container is **neo4j version 3.5.x**. To build the container for X86, invoke Charliecloud on the cluster where BEE components will be running to pull the graph database **neo4j** and create a Charliecloud tarball.


.. code-block::

        ch-image pull neo4j:3.5.22
        ch-convert -o tar neo4j:3.5.22 neo4j-3-5-22.tar.gz

..

Installation:
=============

BEE is a PyPI package that can be installed using pip. On an HPC cluster, you may want to set up a miniconda or conda environment or other python environment where you can install beeflow using the following command:

.. code-block::

    pip install hpc-beeflow

If you do not already have a python environment, you may be able to use the following example to create one (note: beeflow-env can be any environment name you choose):

.. code-block::

    mkdir beeflow-env
    python3 -m venv beeflow-env
    source beeflow-env/bin/activate
    pip install hpc-beeflow

You will need to activate the environment with the command ``source beeflow-env/bin/activate`` and type ``deactivate`` when done.


An alternative is to use a Poetry environment, but we suggest this only for contributors.
For more information click on the Developer's Guide in this documentation.

Creating Configuration File:
----------------------------
You will need to setup the bee configuration file that will be located in:

    Linux:  ``~/.config/beeflow/bee.conf``

    macOS:  ``~/Library/Application Support/beeflow/bee.conf``

Before creating a bee.conf file you will need to know the path to your **BEE
dependency container** and the type of workload scheduler (Slurm or LSF). (On
LANL systems you may use the BEE provided container:
**/usr/projects/BEE/neo4j-3-5-17-ch.tar.gz**). Depending on the system, you
may also need to know an account name to use.

Once you are ready type ``beecfg new``.

The bee.conf configuration file is a text file and you can edit it for your
needs.

**Caution: The default for container_archive is in the home directory. Some
systems have small quotas for home directories and containers can be large
files.**

**beecfg** has other options including a configuration validator. For more
information or help run: ``beecfg info`` or ``beecfg --help``.

Starting up the BEE components:
-------------------------------

To start the components (scheduler, slurmrestd(SLURM only), workflow manager, and task manager) simply run:

.. code-block::

    beeflow start

To check the status of the bee components run:

.. code-block::

    beeflow status

.. code-block::

    beeflow components:
    scheduler ... RUNNING
    slurmrestd ... RUNNING
    wf_manager ... RUNNING
    task_manager ... RUNNING

Some HPC systems have multiple front-ends. Run your workflows and components on the same front end.

Stopping the BEE components:
-------------------------------

If at some point you would like to stop the beeflow components, you should first verify that all workflows are complete (archived). (If there are pending workflows, it is also fine to stop the components because you can restart beeflow later and start pending workflows with the "beeclient start" command).

.. code-block::

    beeclient listall

.. code-block::

    Name  ID      Status
    clamr d631d3  Archived
    blast a93267  Pending

Now stop the components.

.. code-block::

    beeflow stop

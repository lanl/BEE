.. _installation:

Installation Guide
******************

This section describes how to install BEE and requirements for installation.

Requirements:
=============

* **Python version 3.8 (or greater)**

* `Charliecloud <https://hpc.github.io/charliecloud/>`_ **version 0.34 (or greater)**
    Charliecloud is installed on Los Alamos National Laboratory (LANL) clusters and can be invoked via ``module load charliecloud`` before running beeflow. If you are on a system that does not have the module, `Charliecloud <https://hpc.github.io/charliecloud/>`_ is easily installed in user space and requires no privileges to install. To insure Charliecloud is available in subsequent runs add ``module load charliecloud`` (or if you installed it ``export PATH=<path_to_ch-run>:$PATH``) to your .bashrc (or other appropriate shell initialization file). BEE runs dependencies from a Charliecloud container and uses it to run the graph database neo4j and other dependencies. The default container runtime for containerized applications in BEE is Charliecloud.


* **Containers**:
    Two Charliecloud dependency containers are currently required for BEE: one for the Neo4j graph database and another for Redis. The paths to these containers will need to be set in the BEE configuration later, using the ``neo4j_image`` and the ``redis_image`` options respectively. BEE only supports Neo4j 3.5.x. We are currently using the latest version of Redis supplied on Docker Hub (as of 2023).

    For LANL systems, please use the containers supplied by the BEE team: **/usr/projects/BEE/neo4j-3-5-17-ch.tar.gz**, **/usr/projects/BEE/redis.tar.gz**.

    For other users, these containers can be pulled from Docker Hub and converted to a Charliecloud tarball using the following commands:

.. code-block::

        ch-image pull neo4j:3.5.22
        ch-convert -o tar neo4j:3.5.22 neo4j-3-5-22.tar.gz
        ch-image pull redis
        ch-convert -o tar redis redis.tar.gz
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

Before creating a bee.conf file you will need to know the path to the two required Charliecloud containers, one for Neo4j (``neo4j_image``) and Redis (``redis_image``). See `Requirements:`_ above for pulling these containers. Depending on the system, you may also need to know system-specific information, such as account information. You can leave some options blank if these are unnecessary.

Once you are ready type ``beeflow config new``.

The bee.conf configuration file is a text file and you can edit it for your
needs.

**Caution: The default for container_archive is in the home directory. Some
systems have small quotas for home directories and containers can be large
files.**

**beeflow config** has other options including a configuration validator. For more
information or help run: ``beeflow config info`` or ``beeflow config --help``.

Starting up the BEE components:
-------------------------------

To start the components (scheduler, slurmrestd(SLURM only), workflow manager, and task manager) simply run:

.. code-block::

    beeflow core start

To check the status of the bee components run:

.. code-block::

    beeflow core status

.. code-block::

    beeflow components:
    scheduler ... RUNNING
    slurmrestd ... RUNNING
    wf_manager ... RUNNING
    task_manager ... RUNNING

Some HPC systems have multiple front-ends. Run your workflows and components on the same front end.

Stopping the BEE components:
-------------------------------

If at some point you would like to stop the beeflow components, you should first verify that all workflows are complete (archived). (If there are pending workflows, it is also fine to stop the components because you can restart beeflow later and start pending workflows with the "beeflow start" command).

.. code-block::

    beeflow list

.. code-block::

    Name  ID      Status
    clamr d631d3  Archived
    blast a93267  Pending

Now stop the components.

.. code-block::

    beeflow core stop

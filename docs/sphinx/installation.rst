Installation Guide
******************

This section describes how to install BEE and requirements for installation.

Requirements:
=============

    * **Python version 3.8** (or greater)

    * `Charliecloud <https://hpc.github.io/charliecloud/>`_ **version 0.27** (or greater)
        Charliecloud is installed on LANL clusters and can be invoked using the module command. Charliecloud is also easily installed in user space and requires no privilege to install. BEE runs dependencies from a Charliecloud container and uses Charliecloud to run the graph database neo4j and other dependencies. The default container runtime for containerized applications in BEE is Charliecloud.


    * **BEE dependency container**:
        If you are on a LANL system there you may use the dependency container supplied by the BEE team. The path is **/usr/projects/BEE/neo4j-3-5-17-ch.tar.gz**

        At this time the only dependency needed in a container is **neo4j version 3.5.x**. To build the container for X86. Invoke Charliecloud on the cluster where BEE components will be running to pull the graph database **neo4j** and create a Charliecloud tarball.


.. code-block::

        ch-image pull neo4j:3.5.22
        ch-convert -o tar neo4j:3.5.22 neo4j-3-5-22.tar.gz (or path of your choice)

        Add the path to the bee.conf file in the Default section as:

            bee_dep_image = (path to neo4j-3-5-22.tar.gz)

Installation:
=============

BEE is a PyPI package that can be installed using pip. On an HPC cluster you may want to set up a miniconda or conda environment or other python environment where you can install beeflow using the following command.

.. code-block::

    pip install beeflow

An alternative is to use a Poetry environment, but we suggest this only for developers.
For more information click on the Developer's Guide in this documentation.

Creating Configuration File:
----------------------------
You will need to setup the bee configuration file that will be located in:

    $HOME/.config/beeflow/bee.conf

Before creating a bee.conf file you will need to know the path to your **BEE dependency container**, and the type of workload scheduler (Slurm or LSF). Once you are ready type ``bee_cfg new``

The bee.conf configuration file is a text file and you can edit it to suit your needs. You may list the contents by typing ``bee_cfg list``.


**Caution: the default for container_archive is in the home directory. Some systems have small quotas for home directories and containers can be large files.**

**bee_cfg** has other options including a configuration validator. For more options run ``bee_cfg info``

Starting up the BEE components:
-------------------------------

To start the components, workflow manager, task manager, graph database and scheduler
simply run:

.. code-block::

    beeflow

.. code-block::

    INFO: Starting slurmrestd based on userconfig file.
    INFO: Loading Scheduler
    INFO: Loading Workflow Manager
    INFO: Loading Task Manager


Some HPC systems have multiple front-ends. Run your workflows and components on the same front end.





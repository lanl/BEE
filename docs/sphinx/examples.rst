Getting Started - Example Workflows
***********************************

If you have beeflow installed and the components running you are ready to try out a BEE workflow.

CLAMR workflow examples
=======================
`CLAMR <https://github.com/lanl/CLAMR>`_ is an open source LANL mini-app that simulates shallow water equations. CLAMR performs hydrodynamic cell-based adaptive mesh refinement (AMR).

The CLAMR workflow examples we introduce here are simple two step workflows that run a CLAMR simulation in step one, producing graphic images from periodic time steps. Then FFMPEG is run in step two to make a movie visualizing the progression of the simulation. We use these workflows for some of our integration tests and they are practical examples to help you start using BEE. The differences in the clamr workflows are the way the containers are used.

    - **CLAMR build workflow** the container will be built
    - **CLAMR copy workflow**, the container will be copied from a specified path to the container_archive directory (specified in bee.conf)
    - **CLAMR use workflow** uses the container specified

CLAMR build workflow
--------------------
The workflow is in **examples/clamr-ffmpeg-build.tgz**. You may want to explore the cwl files in **examples/clamr-ffmpeg-build** to understand the workflow specification for the example. Below is the clamr-step with the DockerRequirement in hints that specifies to build a container from a dockerfile using Charliecloud (the container runtime specified in the configuration file).

CWL for clamr step in examples/clamr-ffmpeg-build/clamr_wf.cwl

.. image:: clamr-step.png



Submit the CLAMR workflow on the same front end, where you started the components (to start the components of beeflow, see Installation Guide).

.. code-block::

    cd <to the directory containing clamr-ffmpeg-build.tgz>
    bee_client submit example clamr-ffmpeg-build.tgz clamr_wf.cwl clamr_job.yml

Output:

.. code-block::

   Workflow submitted! Your workflow id is fce80d.


Start workflow using the workflow id from the output:

.. code-block::

    bee_client start fce80d # use the actual workflow id

Output:

.. code-block::

    Started workflow!

If this is the first time you've run the workflow it will build the container and create a Charliecloud image tarball. This process will be done before running the workflow tasks as jobs and may take a few minutes. The first task will be in the ready state, until the container is built. This is the pre-processing building phase and will only be performed once. In this example both steps use the container that is built in the pre-processing stage. Once the build has been completed the Charliecloud image will be in the container archive location specified in the builder section of the bee configuration file. You can list contents of the configuration file using ``bee_cfg list``. The status of the workflow will progress to completion and can be queried as shown:


Check the status:

.. code-block::

    bee_client query fce80d

Output:

.. code-block::

    Running
    clamr--READY
    ffmpeg--WAITING

Check the status:

.. code-block::

    bee_client query fce80d

Output:

.. code-block::

    Running
    clamr--RUNNING
    ffmpeg--WAITING

When completed:

.. code-block::

    bee_client query fce80d

Output:

.. code-block::

    Archived
    clamr--COMPLETED
    ffmpeg--COMPLETED

The archived workflow with associated standard job outputs will be in the **bee_workdir** see the default section of your configuration file (to list configuration file contents run ``bee_cfg list``). This workflow also produces output from CLAMR and ffmpeg in your home directory:

.. code-block::

    graphics_output - a directory containing the graphics png files.
    total_execution_time.log
    CLAMR_movie.mp4 - The final movie

The other outputs are in the archive of the workflow.

This example uses Charliecloud. The image will still be in the Charliecloud cache. You can list what is in the cache using ``ch-image list``.  If there are no other builds, the result should be:

.. code-block::

    ch-image list

.. code-block::

    clamr-ffmpeg
    debian:stable-slim

There are other commands for resetting (clearing out all images) and deleting an image. Type ``ch-image --help`` for more information or read the [Charliecloud documentation](https://hpc.github.io/charliecloud/).

CLAMR copy workflow
--------------------
Add LANL example here copying /usr/projects/BEE/clamr/clamr-toss ...

CLAMR use workflow
--------------------
Add LANL example here using /usr/projects/BEE/clamr/clamr-toss ...






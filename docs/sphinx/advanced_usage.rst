Advanced Usage
**************

Command and Job Output
----------------------

When BEE submits steps of a workflow, by default the output from the underlying
batch scheduler (Slurm, LSF, etc.) will be saved by BEE. This includes all
output from other helping programs, such as the container runtime and the batch
scheduler itself. Sometimes this output can be useful when diagnosing runtime
failures. In most cases you shouldn't need to use this unless the error is
outside of your program (this often includes environment-related and
setup/installation issues). Note, to allow for better provenance, this output
is also saved when archiving a workflow. This is also one reason why the
specific path below should not be changed unless you know what you're doing.

By default, output from job, if not captured by an ``stdout`` or an ``stderr``
option within your workflow CWL will be directed to
``$bee_workdir/workflows/$workflow_id/$task_name-$task_id``,
with the meaning of each component listed below:

``$bee_workdir``
    BEE's workdir, which is set in the bee.conf file and by default is
    ``$HOME/.beeflow``
``$workflow_id``
    The same ID used to start the workflow
``$task_id``
    A randomly generated UUID which BEE uses to keep track of the task
``$task_name``
    The task/step name used within the workflow submission

Within this directory, you can find the submission script and two output files
for stderr (extension ``.err``) and stdout (extension ``.out``).

If something bad happens, such as if BEE fails unexpectedly, then you may need
to examine these output files. Sometimes the error may have to do with the
environment or with a task's requirements. If you're unable to find the cause
of the problem, then you should contact the BEE developers.

.. _Multiple Workflows:

Multiple Workflows
---------------------

BEE allows orchestration of multiple workflows. You can try running concurrent
example workflows from :ref:`Simple example` with two different names and
different output paths. Using the same example is over simplified
but does demonstrate running concurrent workflows. You may have requirements
where you run the same workflow with different inputs and paths for outputs or
other variations. You could prepare a workflow with different yaml files and
make submissions for each specification.  We suggest you use unique names for
each workflow, but it isn't necessary since BEE assigns a unique workflow ID to
each one.  For demonstration we show how you might run our simple example as
two workflows with different names.

The procedure would be to submit some workflows like the following:

.. code-block::

    mkdir results1
    mkdir results2
    beeclient submit cgt1 ./cat-grep-tar.tgz workflow.cwl input.yml results1
    beeclient submit cgt2 ./cat-grep-tar.tgz workflow.cwl input.yml results2
    beeclient listall

.. code-block::

    Name  ID      Status
    cgt1  b33fd3  Pending
    cgt2  9a378c  Pending

You could then start each workflow with the ``beeclient start <WFID>`` command and query for the status of their tasks separately using ``beeclient query <WFID>``.


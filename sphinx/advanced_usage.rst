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

When using the default template (see `Jinja file`_), outputs from the batch
script will go to files in
``$bee_workdir/workflows/$workflow_id/$task_name-$task_id``:

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

By default when you run ``beecfg new``, a default template file will be
generated for you, not unlike the one above.  The default template for Slurm
accepts the number of nodes and the number of tasks and submits corresponding
``#SBATCH`` directives for the job. You may also add other ``#SBATCH`` (or for
LSF ``#BSUB``) directives to your jinja file, to use a specific partition or
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

Check the bee configuration file (bee.conf) or type ``beecfg show`` for the
current location of your job_template. If you need to, edit it for your
particular needs.

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


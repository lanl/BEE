Writing BEE workflows
=====================

BEE supports two equivalent workflow front ends: a Python file and a versioned
YAML file. Submit **either file**, not both. YAML is not an additional settings
file for Python workflows. Both front ends use the same validation, execution
models, dependency graph and workers. CWL remains available through an optional
compatibility adapter; see :doc:`workflow_formats` for installation and extensions.

Quick start
-----------

Save the following as ``workflow.yaml``:

.. code-block:: yaml

   bee_version: 1
   tasks:
     message:
       commands: echo {message}
       params:
         message: Hello from BEE
       stdout: message.txt
       outputs:
         contents: message.txt

     copy:
       commands: cat {text_file}
       inputs:
         text_file: {from: message/contents}
       stdout: copied.txt
       outputs:
         contents: copied.txt

The equivalent ``workflow.py`` is:

.. code-block:: python

   from beeflow.common.workflow_api import Workflow

   workflow = Workflow("message-copy")
   message = workflow.add_task(
       name="message",
       commands="echo {message}",
       params={"message": "Hello from BEE"},
       stdout="message.txt",
       outputs={"contents": "message.txt"},
   )
   workflow.add_task(
       name="copy",
       commands="cat {text_file}",
       inputs={"text_file": message.output("contents")},
       stdout="copied.txt",
       outputs={"contents": "copied.txt"},
   )

With BEE configured and core running on a supported execution environment:

.. code-block:: sh

   beeflow submit workflow.yaml
   # Or, instead:
   beeflow submit workflow.py

A separate job-input file is **not required**. This example generates its own
data. A workflow referencing datasets, scripts or container images still needs
those resources to be accessible. Single-file submission packages the
specification and an explicitly supplied job file, not arbitrary neighboring
files. Use a workflow directory or archive when packaging supporting files.
Input datasets are not automatically staged into task workdirs.

Validate and inspect without submitting to running services:

.. code-block:: sh

   python -m beeflow.common.parser workflow.yaml

See ``examples/yaml-workflow/workflow.yaml`` for a complete self-contained YAML
example including an explicit dependency and multiple commands. The Python
example is ``examples/cat-grep-tar/workflow.py``.

YAML document reference
-----------------------

.. list-table:: Top-level fields
   :header-rows: 1
   :widths: 22 24 54

   * - Field
     - Type / default
     - Meaning
   * - ``bee_version``
     - Integer, required; must be ``1``
     - Identifies a workflow document, rather than a job-input file. The string
       ``"1"`` and boolean ``true`` are not version numbers.
   * - ``name``
     - String; defaults to the file stem
     - Specification name used by the parser when no name is supplied.
       ``beeflow submit`` currently derives its name from the submitted path;
       use ``--name`` to override it.
   * - ``description``
     - String; defaults to ``""``
     - Authoring description. Currently not persisted in the runtime workflow
       model; do not rely on it appearing in workflow queries.
   * - ``tasks``
     - Non-empty mapping, required
     - Task names are keys; task options are values. No repeated ``name`` field
       is needed. Tasks may reference tasks declared later in the document.

Unknown fields, duplicate mapping keys and non-string mapping keys are errors.
Task and output names must be non-empty strings without ``/``, which separates
the components of an output reference. YAML loading is safe: Python object
tags, executable tags and multiple documents are not accepted. YAML merge keys
(``<<``) are not supported. Quote strings that YAML would otherwise interpret
as booleans, numbers or dates (for example ``"on"`` or ``"2026-01-01"``).

Task reference (Python and YAML)
--------------------------------

Python: use ``workflow.add_task(name="task", ...)`` or construct a ``Task``
and add it to the workflow. YAML: use the task name as a key under ``tasks``.
The following field names are shared between both front ends.

.. list-table:: Task fields
   :header-rows: 1
   :widths: 22 25 53

   * - Field
     - Type / default
     - Meaning
   * - ``commands``
     - String or non-empty list of strings; required
     - Command text. Multiple commands run sequentially with ``&&`` and stop
       after the first failure. A failed command makes the task fail.
   * - ``params``
     - Mapping; defaults to ``{}``
     - Named scalar values for command placeholders.
   * - ``inputs``
     - Mapping; defaults to ``{}``
     - Named scalar values or references to another task's named output.
   * - ``outputs``
     - Mapping of output names to path/glob strings; defaults to ``{}``
     - Files collected after execution. Also exposed as workflow outputs.
   * - ``depends_on``
     - YAML: list of task names. Python: list of Task objects. Defaults to none.
     - Explicit ordering without sharing data. Referenced tasks must belong
       to this workflow. Data references already create dependency edges.
   * - ``resources``
     - YAML: mapping. Python: ``Resources``. Optional.
     - Resource settings listed below.
   * - ``scheduler_options``
     - Mapping; defaults to none
     - Scheduler-specific options, e.g. ``account``, ``partition``, ``qos``.
       Values are scalars (``null`` skips an option). Currently emitted as Slurm
       hints; availability depends on the scheduler.
   * - ``container``
     - Image string, or YAML mapping / Python ``Container``. Optional.
     - Container image, optional bind mounts and requirement behavior; see below.
   * - ``workdir``
     - Path string; defaults to the workflow working directory
     - Task working directory. Relative paths are resolved under the workflow
       workdir, not the specification directory. Created on task submission.
   * - ``stdout``, ``stderr``
     - Path strings; optional
     - Redirect command output/error to named files under the task workdir.
       If omitted, the worker chooses its normal task-specific log paths.
   * - ``pre_script``, ``post_script``
     - Path strings; optional
     - Script files read relative to the specification, run before/after the
       command. Their shebang must match ``/bin/bash``.

Omit unused optional fields in YAML rather than supplying ``null``. Scalars in
``params`` and ``inputs`` may be strings, integers, floats or booleans; arbitrary
lists/dictionaries and dates are not supported as input values. An explicit
output-reference mapping is the exception. An input overrides a param of the
same name, matching the Python API.

Placeholders and input overrides
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use ``{name}`` in command text to substitute the corresponding param/input
value at execution time. Embedded placeholders such as ``--label={name}`` are
also supported. Every placeholder must have a declared value or reference.
Commands are shell-oriented text, not an argv serialization format, and
substitutions are not a shell-escaping boundary. Use trusted values and explicit
shell quoting where necessary; no new quoting semantics are introduced by YAML.

A name declared consistently among the tasks using it becomes a workflow input;
conflicting declarations stay task-local. To override workflow input values,
optionally create ``job.yaml``:

.. code-block:: yaml

   message: A replacement message

.. code-block:: sh

   beeflow submit workflow.yaml --job job.yaml

Job-input files contain value mappings, **not** ``bee_version`` or ``tasks``
workflow wrappers. They can be YAML or JSON. ``bee_version`` is reserved for
workflow identification in YAML files. Unknown override names are currently
ignored by the shared parser, so check spelling carefully.

Dependencies and references
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   inputs:
     data: {from: producer/result}
     literal_path: producer/result
   depends_on: [setup]

Only the mapping form is an output reference; the plain string is literal.
The reference must contain exactly one ``/`` and point to an existing task and
output. The same reference form is also accepted in ``params``, matching the
Python API's support for output references among declared values.
In Python, use ``producer.output("result")`` instead of the YAML mapping.

Missing references, missing placeholders, and cycles involving data references,
explicit dependencies or both are errors. Explicit dependencies hold a task
until the dependency reaches a final state; a failed predecessor is handled
through dependency-failure propagation, not treated as successful execution.

Checkpoint restarts create a new task ID and change its display name (for example,
``setup`` becomes ``setup-1``). Existing dependency edges are transferred by task
ID, not resolved again from display names. Both data-flow and explicit edges
retain their classification, and explicit dependents wait for the replacement
attempt. The authored ``depends_on`` names remain the original specification
names; they are not rewritten to attempt names. This does not broaden the READY
gate to data-only edges.

Resources
~~~~~~~~~

.. code-block:: yaml

   resources:
     nodes: 1
     ntasks: 4
     tasks_per_node: 4
     walltime: "00:10:00"
   scheduler_options:
     account: my-account
     partition: debug

The Python equivalent is ``Resources(nodes=1, ntasks=4, tasks_per_node=4,
walltime="00:10:00")``. Import ``Resources`` from
``beeflow.common.workflow_api``. All fields are optional. YAML counts must be
positive integers; ``walltime`` must be a string. These become existing MPI and
Slurm hints; scheduler/site support determines how they are applied.

Containers
~~~~~~~~~~

An image string such as ``container: debian:12`` is a best-effort container hint.
For more control:

.. code-block:: yaml

   container:
     image: debian:12
     bind_mounts:
       /host/data: /data
     required: true

Python: ``Container(image="debian:12", bind_mounts={"/host/data": "/data"},
required=True)``, imported from ``beeflow.common.workflow_api``.

``image`` is required in the mapping. ``bind_mounts`` defaults to ``{}`` and
maps host paths to container paths; both must be strings. ``required`` defaults
to ``false``. Set it to ``true`` for a mandatory DockerRequirement rather than
a best-effort hint. Actual fallback/failure behavior is handled by the existing
build/container runtime; YAML does not change it.

Registry references become ``dockerPull`` settings. Local image files use the
existing ``beeflow:useContainer`` path handling. Local paths and recognized image
extensions are interpreted as local images; this is not image-format validation.
Containers require an appropriate runtime and execution environment.

File selection and paths
------------------------

.. code-block:: sh

   beeflow submit workflow.yaml
   beeflow submit workflow-directory
   beeflow submit workflow-package.tgz

Directory/archive discovery treats Python and marked YAML files as BEE workflow
candidates. If more than one exists, select the main file explicitly with
``--main-cwl`` (the existing option name is retained during migration). BEE
specifications are preferred over legacy CWL candidates. Workflow YAML is never
automatically selected as a job-input file. Multiple job-input candidates
require ``--job``. A supplied job file must not overwrite the specification
filename during single-file packaging.

``--name``, ``--workdir`` and ``--no-start`` remain available. The default
workflow workdir is ``~/.beeflow/workflows/<name>`` when ``~/.beeflow`` exists,
otherwise ``./bee-workflows/<name>``. Workflow workdirs cannot be under ``/tmp``
or ``/var/tmp``, including symlinks into them. Relative command paths resolve
inside each task workdir. Declared relative output globs also resolve there.

Submission packages a workflow description; it does not guarantee the runtime
can access an external file. Directory packaging includes supporting files,
but does not by itself copy input datasets into task working directories.

Validation and limitations
--------------------------

For a reproducible live BEE smoke test, including isolated Linux Docker setup,
expected outputs, troubleshooting and shutdown, see :doc:`workflow_testing`.

.. code-block:: sh

   python -m beeflow.common.parser workflow.yaml
   pytest beeflow/tests/test_yaml_workflow.py -q

Validation errors identify the source file/task/field where available. The YAML
loader checks document structure and converts to Python API objects. BeeParser
then applies shared placeholder, dependency and cycle validation. Neither format
requires generating CWL. YAML itself cannot execute Python to generate tasks;
use a Python workflow for loops or programmatic construction.

Workflow-level resource defaults, arbitrary metadata, nested workflows, and new
scheduler/container execution semantics are outside this YAML front end. See
``docs/cwl-migration-plan.md`` for migration status and remaining Linux/HPC
validation. Passing local tests is not equivalent to full scheduler/container
integration validation.

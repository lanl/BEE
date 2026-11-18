Workflow formats and extensions
===============================

BEE accepts workflows through a common format-adapter boundary. Python and
versioned BEE YAML are built in. CWL remains supported as a compatibility format
with optional installation dependencies; it has not been removed or silently
converted to a different workflow language.

Install optional CWL support
-----------------------------

For an installation providing this version of BEE:

.. code-block:: sh

   pip install 'hpc-beeflow[cwl]'

From a development checkout, with the virtualenv activated:

.. code-block:: sh

   poetry install --extras cwl

The extra installs ``cwl-utils`` and the ``ruamel.yaml`` dependency needed by the
older Python CWL-generation API. The default runtime dependency set does not
include these packages. Development tools such as ``cwltool`` may independently
pull in CWL dependencies, so a developer environment is not proof that a clean
core-only installation works without them.

Python/YAML parsing, discovery and CLI imports do not import CWL packages.
Requesting CWL parsing without the extra produces an installation diagnostic.
Existing imports remain supported:

.. code-block:: python

   from beeflow.common.parser import BeeParser, CwlParser, CwlParseError

The compatibility parser implementation remains in its historical module for
now. Its external CWL dependencies are loaded only when CWL parsing is actually
requested. Existing ``beeflow.common.cwl.workflow`` authoring/generation code is
also retained; using that older API requires the optional CWL dependencies.

Existing CWL workflows
----------------------

.. code-block:: sh

   beeflow submit my-workflow-directory --main-cwl my-workflow-directory/workflow.cwl
   beeflow submit my-workflow.tgz
   # Direct CWL submission also packages neighboring run files:
   beeflow submit my-workflow-directory/workflow.cwl
   python -m beeflow.common.parser my-workflow-directory/workflow.cwl -i job.yaml

The same CWL parser and its existing supported feature set are used. This is not
a promise to support every construct in the CWL standard. Job inputs, linked
``run`` files and existing build/scheduler hints retain their current behavior.
Direct CWL-file submission packages the **entire parent directory** and
auto-detects job inputs there; use a dedicated workflow directory to avoid
including unrelated or large files.

The archive layout and saved ``main_cwl``/``yaml`` metadata keys have not changed
in this adapter slice. Reexecution still delegates to submission, which selects
the installed adapter for the archived main file. Existing CWL archives remain
usable with the CWL extra installed. An archive from an external format also
requires its adapter to be installed; adapter code is not embedded in the archive.

Discovery rules
---------------

The built-in formats are:

.. list-table:: Built-in readers
   :header-rows: 1

   * - Name
     - Identification
     - Directory priority
   * - ``python``
     - ``.py`` suffix
     - 0
   * - ``yaml``
     - ``.yaml`` / ``.yml`` and top-level ``bee_version``
     - 0
   * - ``cwl``
     - ``.cwl``, or ``.yaml`` / ``.yml`` / ``.json`` with top-level ``cwlVersion``
     - 10

Lower directory priority wins, preserving native BEE-before-CWL discovery.
Multiple files at the winning priority require explicit main-file selection
with the existing ``--main-cwl`` option. Multiple adapters claiming the *same*
file are an error, not a priority-based silent override. Installed extensions
should use distinct suffixes or disjoint content probes.

Recognized workflows are excluded from job-input candidates, including marked
CWL YAML/JSON and installed formats. Only unrecognized YAML/JSON files are
considered for automatic job-input selection. Content probes use safe YAML
loading and never execute specification code. Full format validation happens
after selection; an unsupported version marker must not be treated as job data.

Writing an extension
--------------------

An installed extension exports a ``WorkflowFormat`` descriptor, or a no-argument
factory returning one, through the ``beeflow.workflow_formats`` package entry
point group. The contract is defined in
``beeflow.common.parser.formats``.

Example module ``my_bee_format.py``:

.. code-block:: python

   from pathlib import Path
   from beeflow.common.object_models import Task, Workflow
   from beeflow.common.parser.formats import WorkflowFormat

   def parse(workflow_id, workflow_name, spec, job=None, workdir=".", wf_path="."):
       # Import any optional format-specific dependencies here, not at module
       # import time or inside the content probe.
       message = Path(spec).read_text(encoding="utf-8").strip()
       workflow = Workflow(
           id=workflow_id, name=workflow_name or Path(spec).stem,
           main_cwl=str(spec), yaml=job, workdir=workdir, wf_path=str(wf_path),
       )
       task = Task(
           name="message", workflow_id=workflow_id, base_command=["echo", message],
           workdir=workdir,
       )
       return workflow, [task]

   adapter = WorkflowFormat(
       name="message-file", extensions=(".beemsg",), parse=parse,
   )

Declare the entry point in the extension package (PEP 621 example):

.. code-block:: toml

   [project.entry-points."beeflow.workflow_formats"]
   message-file = "my_bee_format:adapter"

With Poetry metadata, the equivalent group is
``[tool.poetry.plugins."beeflow.workflow_formats"]``. Install that package into
the same environment as BEE. A ``.beemsg`` file can then be submitted directly,
through directory/archive submission, or parsed with the package parser CLI.
The example's command values use BEE's existing shell-oriented semantics; this
is not a shell-escaping or untrusted-input example.

Descriptor fields:

* ``name``: unique format name. Replacing a built-in name is rejected.
* ``extensions``: non-empty tuple of lowercase suffixes, including the dot.
  ``.tgz`` is reserved for BEE workflow archives.
* ``parse``: callable accepting the arguments shown above. It must return
  ``(beeflow.common.object_models.Workflow, list[Task])``, not authoring-layer
  objects. Workflow/task IDs, references and execution requirements must be
  normalized by the adapter.
* ``probe``: optional callable accepting a ``pathlib.Path`` and returning whether
  the file belongs to the format. Keep it cheap, non-executing and independent
  of optional parsing packages.
* ``discovery_priority``: integer, default ``0``. Applies only to choosing among
  different main-file candidates in a directory.
* ``bundle_directory``: boolean, default ``False``. When true, direct-file
  submission packages the parent directory and its resources, as CWL does.
  Otherwise it packages just the main file and an explicitly supplied job file.

The registry checks return model types and reports parser/probe errors with
format context. It does not supply missing execution semantics: an adapter is
responsible for translating its source format faithfully and rejecting
unsupported constructs. No additional package/asset-staging hooks are defined
in this initial read-adapter contract.

An adapter can build ``beeflow.common.workflow_api.Workflow`` authoring objects
and delegate their validation/conversion to ``BeeParser`` rather than duplicating
that logic. It must return the resulting execution models to the registry.

.. warning::

   Installed adapters are trusted Python code. Loading entry points imports
   that code; this is not the same security boundary as reading a safe YAML
   workflow. A broken installed extension is reported rather than silently
   ignored, and can block registry construction until repaired or uninstalled.

For programmatic use, create a ``FormatRegistry``, register descriptors, and call
``resolve(path)`` or ``discover(directory)``. ``resolve(path, format_name=...)``
permits explicit programmatic selection. The submission CLI does not yet expose
a format-name override; ``--main-cwl`` selects a file, not an adapter.

Testing and remaining work
--------------------------

.. code-block:: sh

   poetry install --extras cwl
   pytest beeflow/tests/test_workflow_formats.py beeflow/tests/test_parser.py \
     beeflow/tests/test_bee_parser.py beeflow/tests/test_bee_client.py -q

Tests cover optional-import isolation, installed entry points, discovery,
normalized execution models, linked CWL tools, and custom-format reexecution.
See :doc:`workflow_testing` for service-stack tests. The adapter boundary does
not change scoped dependency readiness or scheduler/runtime behavior.

Core metadata renaming and a conversion/export command are separate subsequent
phase-4 work. Adapters currently declare **reading**, not writing capabilities.
The planned converter will infer output format from ``--output`` and allow a
``--to`` override with a mismatch warning; no conversion CLI is provided yet.

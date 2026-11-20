Testing Python/YAML workflows
=============================

This guide covers parser checks, regression tests and a real BEE service-stack
smoke test for the YAML front end. For the schema and authoring tutorial, see
:doc:`workflow_spec`.

Parser and regression tests
---------------------------

From the repository root, activate your development virtualenv, then run:

.. code-block:: sh

   # Include optional compatibility dependencies for the complete test suite:
   poetry install --extras cwl
   python -W error::RuntimeWarning -m beeflow.common.parser \
     examples/yaml-workflow/workflow.yaml
   pytest beeflow/tests/test_yaml_workflow.py -q
   pytest beeflow/tests/ -q --ignore=beeflow/tests/test_slurm_worker.py
   pylint --rcfile=setup.cfg beeflow

The parser command only prints workflow/task models; it does not execute any
commands. Use the package entry point ``beeflow.common.parser``, rather than
``beeflow.common.parser.parser``, to avoid the runpy warning caused by executing
an already-imported module.

The reduced suite above deliberately excludes tests that require a real Slurm
environment. Tests in ``test_phase2_neo4j.py`` also skip unless their live Neo4j
connection is explicitly configured. Run the full suite on an appropriately
configured host before claiming Slurm/HPC validation:

.. code-block:: sh

   pytest beeflow/tests/ -q

The YAML tests cover schema validation, duplicate-key/unsafe-tag rejection,
Python/YAML model parity, forward references, cycles, command-line parsing,
and local worker execution. Client tests also cover direct-file, directory and
archive submission with and without job-input overrides.

Smoke test with an existing BEE instance
----------------------------------------

On a configured execution host with BEE running:

.. code-block:: sh

   beeflow core status
   beeflow submit examples/yaml-workflow/workflow.yaml \
     --name yaml-smoke --workdir "$HOME/bee-runs/yaml-smoke"
   beeflow list
   # Replace <workflow-id> with the ID printed by submit:
   beeflow query <workflow-id>

Wait for all three tasks (``message``, ``copy``, ``finish``) to become
``COMPLETED``. The workflow will normally move to ``Archived`` after successful
execution. Confirm that the data dependency propagated the original message:

.. code-block:: sh

   cmp "$HOME/bee-runs/yaml-smoke/message.txt" \
       "$HOME/bee-runs/yaml-smoke/copied.txt"
   cat "$HOME/bee-runs/yaml-smoke/copied.txt"

``cmp`` should exit successfully without output. ``copied.txt`` should contain
``Hello from BEE``. The ``finish`` task's output should contain both
``Copy completed`` and ``Workflow completed``. Use a new name and working
directory for independent repeated runs, rather than overwriting old outputs.

Isolated Linux Docker demonstration
-----------------------------------

This alternative works from macOS with a running Linux Docker engine, or from
a Linux Docker host. It runs real Redis, Celery, Workflow Manager, Task Manager,
SQLite and Simple worker processes. The source checkout is mounted read-only;
configuration, installed dependencies and run data stay inside the container.
No host BEE configuration is created or modified, and no network ports are
published.

.. warning::

   This is a local development demonstration, not a production deployment.
   It runs as root inside the container, including a root-enabled Celery worker.
   It exercises bare-metal task commands **inside Linux Docker**, not Slurm/Flux
   scheduling or task-level container image execution. Those need separate tests
   on supported execution hosts. Setup downloads system and Python dependencies
   and consumes container disk space.

Create and install a fresh instance
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Run these commands from the root of the checkout containing the YAML changes.
If ``bee-yaml-e2e`` already exists, either use the existing instance as described
below or choose another container name consistently throughout these commands.
Do not remove an existing instance without checking its run data first.

.. code-block:: sh

   docker run -d --name bee-yaml-e2e \
     --mount "type=bind,source=$PWD,target=/workspace,readonly" \
     --workdir /workspace -e USER=root -e C_FORCE_ROOT=1 \
     python:3.12-slim-trixie sleep infinity

   docker exec -i bee-yaml-e2e bash <<'SH'
   set -e
   apt-get update
   DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
     charliecloud redis-server graphviz procps
   python -m venv /opt/beedev-env
   source /opt/beedev-env/bin/activate
   python -m pip install poetry
   poetry install
   ch-run -V
   beeflow --version
   beeflow config new
   python - <<'PY'
   from configparser import ConfigParser
   from pathlib import Path

   path = Path.home() / ".config/beeflow/bee.conf"
   config = ConfigParser()
   config.read(path)
   config["DEFAULT"].update({
       "bee_workdir": "/root/bee-demo/state",
       "bee_archive_dir": "/root/bee-demo/archives",
       "bee_droppoint": "/root/bee-demo/drop",
       "workload_scheduler": "Simple",
       "use_redis_container": "False",
       "delete_completed_workflow_dirs": "False",
   })
   config["graphdb"]["type"] = "sqlite3"
   config["builder"]["container_archive"] = "/root/bee-demo/container_archive"
   config["task_manager"]["background_interval"] = "1"
   config["task_manager"]["backup_interval"] = "1"
   # Generated Slurm-only sections are incompatible with the Simple scheduler.
   for section in ("slurm", "slurm attributes", "slurm command attributes"):
       config.remove_section(section)
   with path.open("w") as stream:
       config.write(stream)
   PY
   beeflow config validate
   SH

Charliecloud is installed because BEE's current startup preflight requires it,
even though this example does not request task containers. Activate the virtualenv
before ``poetry install`` so installation targets that environment.

Start services
~~~~~~~~~~~~~~

.. code-block:: sh

   docker exec -d -w / bee-yaml-e2e bash -lc \
     'source /opt/beedev-env/bin/activate; exec beeflow core start --foreground > /root/bee-demo/core-console.log 2>&1'

This runs the documented foreground lifecycle command as a detached Docker exec
process. Run it from ``/``, matching the normal daemon working directory: the
current Celery SQLite result URL otherwise resolves relative to the startup
directory. Foreground mode also avoids a daemon file-descriptor startup failure
observed in the demonstration environment. These are existing startup issues,
not YAML loader workarounds or fixes.

Enter and test the instance
~~~~~~~~~~~~~~~~~~~~~~~~~~~

For a newly started or already running demonstration instance:

.. code-block:: sh

   docker exec -it -w /root bee-yaml-e2e bash
   source /opt/beedev-env/bin/activate
   beeflow core status

Startup is asynchronous; wait for Redis, Celery, Workflow Manager and Task Manager
all to report ``RUNNING`` before submitting. If any component remains failed,
inspect ``/root/bee-demo/core-console.log`` and the component logs under
``/root/bee-demo/state/logs`` rather than treating submission as a successful test.

Inside that shell:

.. code-block:: sh

   beeflow submit /workspace/examples/yaml-workflow/workflow.yaml \
     --name yaml-my-test --workdir /root/bee-demo/runs/yaml-my-test
   beeflow list
   beeflow query <workflow-id>
   cmp /root/bee-demo/runs/yaml-my-test/message.txt \
       /root/bee-demo/runs/yaml-my-test/copied.txt
   cat /root/bee-demo/runs/yaml-my-test/copied.txt
   find /root/bee-demo/runs/yaml-my-test -name 'finish-*.out' -exec cat {} \;

Use the same completion/output checks as in the existing-instance smoke test
above. Submit from ``/root`` (a writable directory), not ``/workspace``: current
packaging creates an archive in the client's working directory before moving
it to its destination.

To test an optional override, still inside the container:

.. code-block:: sh

   printf 'message: Hello from an override\n' > /root/bee-demo/job.yaml
   beeflow submit /workspace/examples/yaml-workflow/workflow.yaml \
     --job /root/bee-demo/job.yaml \
     --name yaml-override --workdir /root/bee-demo/runs/yaml-override
   # Query the new ID until its tasks have completed, then:
   cat /root/bee-demo/runs/yaml-override/copied.txt

Expected output is now ``Hello from an override``. No separate Python workflow
or CWL file is needed for either submission.

Stop and resume
~~~~~~~~~~~~~~~

Inside the container, after workflows have finished:

.. code-block:: sh

   beeflow core stop
   exit

Then on the host:

.. code-block:: sh

   docker stop bee-yaml-e2e

The stopped container retains its environment and results. To resume later,
run ``docker start bee-yaml-e2e``, then repeat the **Start services** command
and enter the instance again. Do not start a second core in an already running
instance. Removing the container discards its internal config, environment and
run data; export any artifacts you need first.

Build documentation
-------------------

.. code-block:: sh

   sphinx-build -b html docs/sphinx /path/to/writable/docs-build

Use a build directory outside the checkout to avoid leaving generated files
among the source changes. Inspect warnings separately from the exit status;
an HTML build can succeed while still reporting documentation warnings.

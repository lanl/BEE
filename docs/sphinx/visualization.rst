.. _workflow-visualization:

Workflow Visualization
**********************

BEE includes a simple command for viewing BEE workflows. By using the ``beeflow
dag $ID $OUTPUT_DIR`` command, you can view the directed acyclic graph (DAG) of any submitted
workflow.

Creating DAGs
=============

The dag command can be run at any point of the workflow, and can
be run multiple times. To see the DAG of a workflow before it runs, submit
the workflow with the ``--no-start`` flag and then use the dag command. The
DAGs are exported in PNG format to $OUTPUT_DIR/$WD_ID-dags by default. If the
``no-dag-dir`` flag is specified when the dag command is run, the DAG will be
exported to $OUTPUT_DIR. The dag command makes multiple versions of the DAGs. The
most recent version is $WF_ID.png and the others are $WD_ID_v1.png,
$WF_ID_v2.png ... where v1 is the oldest. The graphmls used to make the DAGs are saved
in the workflow archive and are saved with their version number. These graphmls can
be useful for debugging when there are errors creating the DAGs.

Example DAG
===========

The DAG below was created by running the dag command while the cat-grep-tar
example workflow was running.

.. image:: images/cat-dag.png

The orange bubbles are inputs, the blue bubbles are task states, the red
bubbles are tasks, and the green bubbles are outputs. The graph is in a
hierarchical format, meaning that tasks that are higher up in the graph
run before the ones below them.

#!/usr/bin/env python3

# This code tests Steven's workflow API and its interfaces to the Neo4j
# graph databse. It also provides a simpe example of hot to use dais API.
# Here we create a simple, two-step, workflow by hand (e.g. not using
# a CWL parser), insert it into the database, and test that dependency
# traversal works (or doesnt).

from beeflow.common.wf_interface import WorkflowInterface


# Open the database using default parameters. You'll obviously need one
# running at the default port. See the documentation on the internal BEE
# GitLab for instructions on how to o this:
#
# https://gitlab.lanl.gov/BEE/database/neo4j
wfi = WorkflowInterface()

# Create some tasks for the workflow. The workflow is very simple:
#
# grep -i string < grep.in > grep.out
# wc -l < grep.out > wc.out
#
# The dependency between the two tasks is specified by shared use of a
# file:
#
# grep ----> grep.out ----> wc
#
# Note that there are no IDs in the tasks at this point. Indeed, the
# current Task interface does not provide a method to set the ID.
tasks = []
tasks.append(wfi.create_task(
    "GREP", command=["grep", "-i", "string"],
    inputs={"grep.in"}, outputs={"grep.out"}))
tasks.append(wfi.create_task(
    "WC", command=["wc", "-l"],
    inputs={"grep.out"}, outputs={"wc.out"}))
print("\n\n==== Tasks as initially created (wfi.create_task):")
print(tasks)

# Create a workflow based on the tasks (as created
# above). create_workflow creates bee_init and bee_exit if they don't
# exist in the list of tasks. It also assigns an ID to each task. It
# determines each task's dependencies and populates an array of
# dependencies for each task (dependencies are represented by the IDs
# of dependent tasks). This is done with Python code (it doesn't use
# the graph databse facilities). In fact, this code does NOT put the
# workflow in the graph database.
wf = wfi.create_workflow(tasks)

# Here we dump the in-memory workflow. Dependencies are specidied by
# task IDs. Everything seems to be correct at this point, except:
#
# Output (ids) DIFFER FROM RUN TO RUN. This is because wf.tasks
# returns a set which was created from a list of tasks in the Workflow
# object. Python (sometimes?) randomizes set manipulation under the
# covers (to fix a security exploit). So, set creation order is
# nondeterministic. Task ids remain deterministic, but task order with
# the set is not (from run to run--diffetent seed).
#
# We could ask, why are we using a set here anyway?
print("\n\n==== Dependencies from Workflow BEFORE load (wfi.create_workflow, not database):")
for t in wf.tasks:
    print("(wf)  ", "id: ", t.id, "name: ", t.name, "deps{ids}: ", t.dependencies)

# Now the workflow (as created above) is inserted into the graph
# databse. Dependencies are created within the database (based on the
# task IDs) and task states are set (all to WAITING). Note here also,
# that the current Task interface has no methods to set ot get a
# task's state.
wfi.load_workflow(wf)
# Set the state of the bee_init task to READY.
wfi.initialize_workflow()
print("\n\n==== Is workflow loaded (wfi.load_workflow)? ", wfi.workflow_loaded())

# At this point there is a duplication of state. We still have the
# workflow as created in memory (wf) and we also have a workflow as
# inserted into the databse (we'll call it wfl, see immediately
# below). Logically, we should ONLY use the graph database version
# from now on. The graph database represents TRUTH. The in-mrmory
# version was ONLY used to populate the database. However, there are
# problems.

# Task IDs are different for these two workflows. That may be OK (an
# artifact of the order in which they're inserted into the databse?)
# as long as the dependencies are set up properly. Dependencies are
# OK.
#
# Output DIFFERS FROM RUN TO RUN because the initial set of tasks
# (above) are ordered nondeterministically.
#
# Maybe the problem: get_workflow pulls tasks from the database and
# then calls create_workflow which reassigns ids to all the tasks. A
# realted issue is that when tasks are pulled from the database, and
# reconstituted into Task objects, ids aren't captured. Both of these
# issues will have to be fixed in Steven's code. The real problem
# might be that we DON'T need a Workflow object to be recreated from
# the databse version. The Workflow object can be used to initialize
# the databse, but from then on maybe we should query the database for
# needed information (dependent tasks, etc.)? Otherwise, every time we
# suspect a change in database state, we need to call get_workflow()
# and create another (newer) in-memory Workflow.
print("\n\n==== Dependencies from Workflow AFTER load (wfl:loaded):")
wfl = wfi.get_workflow()
for t in wfl.tasks:
    print("(wfl) ", "id: ", t.id, "name: ", t.name, "deps{ids}: ", t.dependencies)

# Fake an orchestrator loop.  As far as I can see, there is no method
# to get the bee_init task (this will need to be added to the workflow
# interface API).
#
# Here we query the database workflow and, for each task, we print the
# task(s) it depends on. We also capture bee_init so we can use it in
# the traversal code (to follow) since its not currently provided by
# the API.
#
# Note that there appears to be no state property in the Task
# object. State seems to be carried by the database only. The list of
# dependent tasks is coming from the database, not the property of the
# Task object. Is this duplication managed? There are no IDs in the
# list of dependent tasks?
print("\n\n==== All tasks w/state & get_dependent_tasks (wfl:loaded):")
for t in wfl.tasks:
    print("wfl: {} {}: {}     >> ".format(t.name, t.id, wfi.get_task_state(t)), end="")
    dt = wfi.get_dependent_tasks(t)
    if len(dt) == 0:
        print("Zero")
    else:
        for it in dt:
            print(it.id, it.name)
    if (t.name == "bee_init"):
        wfl_bee_init = t

# This code fails when trying to find the dependent task for GREP?
# It's there in the above code?
print("\n\n==== Chain of dependencies...")
print("... from bee_init (wfl:loaded):")
curr_head = wfl_bee_init
while True:
    # for this hack, we assume only one task!
    dep_tasks = wfi.get_dependent_tasks(curr_head)
    print("[", curr_head.id, curr_head.name, "] --> ", end="")
    if not dep_tasks:
        print("NO MORE")
        break
    next_task = dep_tasks[0]
    curr_head = next_task

# Task manager function


# Clear the workflow that we just built from the database. Comment out if you
# want to take a look at the workflow in the database. Note that if this code
# dies with an error before it gets here you'll have to delete the databse via
# Cypher in the wen interface. This command will do the trick:
#
# MATCH(n) WITH n LIMIT 10000 DETACH DELETE n
wfi.unload_workflow()

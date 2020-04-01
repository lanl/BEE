#!/usr/bin/env python3

# Argument parsing inspired by:
# "Writing sustainable Python scripts"
# https://vincent.bernat.ch/en/blog/2019-sustainable-python-script
#
# cwl-utils repo:
# https://github.com/common-workflow-language/cwl-utils

"""Parse contents a CWL file.

This script will parse (and build a workflow in the databse) the
contents of a CWL file. The CWL file is parsed using parser_v1_0.py
from the cwl-utils repository. That parser creates Python objects from
the CWL file (as opposed to other parsing techniques that produce
Python dictionaries. This graph of Python objects is then traversed
and loaded into the Neo4j databse.

"""

import sys
import argparse
import uuid
import cwl_utils.parser_v1_0 as cwl
from beeflow.common.wf_interface import WorkflowInterface




# Build a Neo4j graph (workflow) from Python object graph (produced by
# prior loading of a CWL file).
def create_workflow(obj, wfi):
    print(f"==== {type(obj)} ====")

    # Get workflow's required inputs and outputs.
    ins = get_wf_inputs(obj.inputs)
    outs = get_wf_outputs(obj.outputs)
    
    # Hack until we refactor databse to do dependencies
    # correctly. Since our current workflow interface supports only
    # single file dependencies, this intermediate file must be
    # removed. This hack will be removed as we refactor the databse
    # interface to correctly support multiple dependencies.
    outs.discard("grep/outfile")
    
    print(f"ins:  {ins}")
    print(f"outs: {outs}")

    # This his here for probable requirement to gather a Docker requirement.
    # for i in obj.requirements:
    #     pass

    # Use workflow interface (note the passed in reference to a Neo4j
    # instance) to instantiate a workflow.
    wfi.initialize_workflow(ins, outs)

    # Now create (and store in the databse) all the workdlow's tasks.
    for i in obj.steps:
        create_task(i, wfi)



# Create task based on the parsed CWL and load it into the Neo4j databse.
def create_task(obj, wfi):
    # Strip off leading garbage from the task name.
    tname = obj.id.split('#')[1]

    ins = set()
    outs = set()

    # Stip the garbase off the front of all task input names.
    for i in obj.in_:
        ins.add(i.source.split('#')[1])

    # Hack until we refactor databse to do dependencies
    # correctly. Since our current workflow interface supports only
    # single file dependencies, this non-file input must be
    # removed. This hack will be removed as we refactor the databse
    # interface to correctly support multiple dependencies (and
    # non-file dependencies).
    ins.discard("pattern")

    # Stip the garbase off the front of all task otput names.
    for i in obj.out:
        outs.add(i.split('#')[1])

    # Build the task's command (which will get sent to the task
    # manager). This is a concatenation of the base command, any input
    # parameters, an input file, and a redirection of stdout to an
    # outpt file.
    base = obj.run.baseCommand
    params = get_task_params(obj.run.inputs)
    # Need to sort the input parameters so they are in the correct
    # order on the command line.
    sorted_params = [value for (key, value) in sorted(params.items())]
    sorted_params_str = ""
    for p in sorted_params:
        sorted_params_str = sorted_params_str + " " + p
    redirect_out = obj.run.stdout
    cmd = base + " " + sorted_params_str + " > " + redirect_out

    # Get any hints for the task. We only support DockerRequirement for now.
    thints = set()
    if obj.run.hints is not None:
        for i in obj.run.hints:
            if "DockerRequirement" in i.values():
                del i["class"]
                for key, value in i.items():
                    thints.add(wfi.create_requirement("DockerRequirement", key, value))

    print(f"task:  {tname}")
    print(f"  ins:      {ins}")
    print(f"  outs:     {outs}")
    print(f"  command:  {cmd}")
    print(f"  hints:    {thints}")

    # Using the BEE workflow interface (note the passed in reference
    # to a Neo4j databse) to load the task nto the database.
    wfi.add_task(name=tname, command=cmd, inputs=ins, outputs=outs, hints=thints)

    

# Get the workflow's inputs as parsed from the CWL file.
def get_wf_inputs(objarray):
    wf_inputs = set()
    for i in objarray:
        if i.type == "File":
            wf_inputs.add(i.id.split("#")[1])
    return wf_inputs



# Get the workflow's inputs as parsed from the CWL file.
def get_wf_outputs(objarray):
    wf_outputs = set()
    for i in objarray:
        id = i.id.split("#")[1]
        source = i.outputSource.split('#')[1]
        wf_outputs.add(source.replace(id + "/", ""))
    return wf_outputs



# Get the task's command parameters as parsed from the CWL file.
def get_task_params(objarray):
    params = {}
    for i in objarray:
        params.update({i.inputBinding.position: i.default})
    return params



# Print array of tasks (as retreived frm Neo4j) to console.
def dump_tasks(tarray, wfi):
    print("-- Tasks: name, IDs (truncated), state, command")
    for t in tarray:
        print(f"{t.name:<12}{str(t.id):<6.5}{wfi.get_task_state(t):<10.9}{t.command}")
        if t.hints is not None:
            print("      hints:")
            for h in t.hints:
                req_class, key, value = h
                print(f"        req_class: {req_class}   key: {key}   value: {value}")
    print("\n-- Tasks: name, dependent tasks")
    for t in tarray:
        print(f"{t.name:<12}", end="")
        for dt in wfi.get_dependent_tasks(t):
            print(f"{dt.name:<12}", end="")
        print("")



# Simple test code to verify a Neo4j workflow.
def verify_workflow(wfi):
    print("\n\n==== Is the workflow loaded?")
    print(wfi.workflow_loaded())

    # Get all the tasks from Neo4j and print them to console.
    (tasks, requirements, hints) = wfi.get_workflow()
    dump_tasks(tasks, wfi)
    
    # Fake a workflow manager loop.  By convention, bee_init is ID 0,
    # bee_exit is ID 1. This little hack only works for workflows
    # where each task has at most one dependent task. In other words,
    # fan in and fan out workflows are not handled here.
    tid = 0
    print(f"{wfi.get_task_by_id(tid).name}", end="")
    while tid != 1:
        print(" --> ", end="")
        # HACK: doesn't handle set sizes greater than one (i.e. fan
        # in, fan out))
        dt = wfi.get_dependent_tasks(wfi.get_task_by_id(tid)).pop()
        print(f"{dt.name}", end="")
        tid = dt.id
    print("")



def parse_args(args=sys.argv[1:]):
    """Parse arguments."""
    parser = argparse.ArgumentParser(description=sys.modules[__name__].__doc__)

    parser.add_argument("cwl_file", type=str, help="CWL file dump")
    return parser.parse_args(args)



def main():
    args = parse_args()

    # Open the database using default parameters. You'll obviously need one
    # running at the default port. See the documentation on the internal BEE
    # GitLab for instructions on how to o this:
    #
    # https://gitlab.lanl.gov/BEE/database/neo4j
    wfi = WorkflowInterface()

    # Load the file into the graph of Python objects representng the workflow.
    top = cwl.load_document(args.cwl_file)

    # Traverse the graph of Python objects and load them into the Neo4j database.
    create_workflow(top, wfi)

    # Run some simple test code to print the representation of the
    # workflow as it exists in the database.
    verify_workflow(wfi)
    
    # Clear the workflow that we just built from the database. Comment out if you
    # want to take a look at the workflow in the database. Note that if this code
    # dies with an error before it gets here you'll have to delete the databse via
    # Cypher in the wen interface. This command will do the trick:
    #
    # MATCH(n) WITH n LIMIT 10000 DETACH DELETE n
    wfi.finalize_workflow()



if __name__ == "__main__":
    sys.exit(main())

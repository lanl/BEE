BEE comes with a CWL library that enables creating CWL files with just Python. 

Each workflow is composed of Task objects.

Each Task object has:
* A name 
* base_command
* stdout and stderr
* A list of Inputs
* A list of Outputs
* An optional hint sections

Input
The input list represent the inputs for a particular Task object. 
Each input has a name, a type ("string", "file", "int"), a source/value, and a position/prefix. 

The name represents 

Output 
The output list represents the outputs for a parituclar task. 
Each output has a name, a type ("stdout", "stderr", "File"), and then option source and glob parameters. 
The source is currently just the name of the task followed by the name of the Output.

Workflow
An actual workflow consists of a workflow name followed by of list of Task objects. 
The write_wf and write_yaml methods on the workflow object write the CWL and YAML file to the specified directory. 
In CMF, this will be the experiment directory. 

Running examples:
If this is your first time running beeflow make sure you run `beeflow config new`. If you have recently upgraded beeflow you may also need to run it.
1.) To run the cat-grep-tar example, copy the cat_grep_tar.py and the lorem.txt files into a working directory. Start beeflow: `beeflow core start` and if you like after a brief pause verify it is running: `beeflow core status`. Create the cat-grep-tar directory: `mkdir cat-grep-tar`
Run the python script: `python3 cat_grep_tar.py`. This will create the cwl and yml input files in the cat-grep-tar directory.

Sumbit the workflow:
`beeflow submit cgt-example cat-grep-tar cat-grep-tar/cat-grep-tar.cwl cat-grep-tar/cat-grep-tar.yml`

beeflow will give you a short workflow id. You can query the status by issuing: `beeflow query <workflow-id>`.

The output files from this example are: cat.txt, occur0.txt occur1.txt and out.tgz.

2.) To run the comd example: copy the comd.py script into a working directory. If you haven't started beeflow, please start it.
Create the comd directory. 
Copy dockerfile, Dockerfile.comd-x86_64 into the comd directory.
Run the script  `python3 comd.py`. This will create the cwl and yml files in the comd directory. 
Submit the workflow:
`beeflow submit comd comd comd/comd.cwl comd/comd.yml .`
The output files from this example : comd.txt (the output of the simulation) and a dated CoMD-mpi yaml file.

beeflow will give you a short workflow id. You can query the status by issui    ng: `beeflow query <workflow-id>`. This example builds a container so the step will be in the 'WAITING' step for a while.

When finished run `beeflow core stop`

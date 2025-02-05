BEE comes with a CWL library that enables creating CWL files with just Python. 

Each workflow is composed of Task objects.

Each Task object has:
* A name 
* base_command
* stdour and stderr
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

To run the cat_grep_tar.py example, simply `mkdir cat-grep-tar` then run the file. 

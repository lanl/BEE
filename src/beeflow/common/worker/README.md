At this point for any tasks that are submitted as jobs, the scripts are left at
~/.beeflow/worker/work-... see ToDo.md

A job template ~/.beeflow/worker/job.template for specific batch type 
requirements for the user (we may get rid of this once we fix requirements).

When a task is submitted task.name and task.id are substituted for
$name and $id in the template. 

An example of job.template:

```
#! /bin/bash

#SBATCH -p galton
#SBATCH -J $name-$id
#SBATCH -o $name-$id.log
```


      

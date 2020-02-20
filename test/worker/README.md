For now: test_slurm_worker.py leaves scripts in ~/.beeflow/worker sub directories.

test_slurm_worker uses job template in ~/.beeflow/worker/job.template
This enables whoever runs these tests to set up a template with requirements
such as account, partition etc.

The substitutions are:  
    fixed for testing submit_job
    substitues task.name and task.id for $name and $id in the template. 

An example of job.template:

```
#! /bin/bash

#SBATCH -p galton
#SBATCH -J $name-$id
#SBATCH -o $name-$id.log
```


      

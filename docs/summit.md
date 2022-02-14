### To run on summit:

```
cd BEE_Private
mkdir -p ~/.beeflow/worker
cp BEE_Private/examples/job_templates/lsf-job.template ~/.beeflow/worker
cp BEE_Private/src/beeflow/data/job_templates/lsf-job.template ~/.beeflow/worker

bin/BEEStart --config-only --workload-scheduler LSF --job-template ~/.beeflow/worker/lsf-job.template
```
### Fix user config file for summit
In  ~/.config/beeflow/bee.conf (or wherever your configuration file is)  
    Fix path of neo4j container  
    Remove or Replace 'setup' in the 'charliecloud' section.  


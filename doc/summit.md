### To run on summit:

```
cd BEE_Private
mkdir -p ~/.beeflow/worker
cp BEE_Private/examples/job_templates/lsf-job.template ~/.beeflow/worker

bin/BEEStart --config-only --workload-scheduler LSF --job-template ~/.beeflow/worker/lsf-job.template
```
### Fix user config file for summit
In  ~/.config/beeflow/bee.conf (or wherever your configuration file is)  
    Fix path of neo4j container  
    Remove or Replace 'setup' in the 'charliecloud' section.  

### Running all components from BEEStart
```
bin/BEEStart
cd beeflow/client
./client.py ( using the cf-summit.cwl)
```

### Run gdb from BEEStart and task_manager and wfm manually for messages
```
bin/BEEStart --gdb
```
Then in separate screens using screen or tmux from BEE_Private
```
beeflow/task_manager/task_manager.py /.config/beeflow/bee.conf
```

```
beeflow/server/server.py /.config/beeflow/bee.conf
```
Now start client and submit the worflow cf-summit.cwl



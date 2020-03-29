This is a preliminary Task Manager. It will submit tasks written to a json file.

Example sent_task.json:

```
task_id": 111
name": "GREP"
command": "grep -i database grep.in  > grep.out"
hints": ""
subworkflow": ""
inputs": "{'grep.in'}":
```


Run test-task-manager.sh to test it, has errors because its testing stuff that 
not work.
```
It may also be helpful to have a job.template on darwin to use the galton nodes,
we have priority on them.

For now task_manager will only run for 2 minutes (edit task_manager.py (timer) for
different times. I did this to ensure I don't leave it running for now.

Leaves scripts in ~/.beeflow/worker, use clean.sh to remove them.


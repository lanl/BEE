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


One way to test the current task manager

```
./clean.sh
python task_manager.py &
./write-tasks-json.sh
```
You and also run the two ls scripts to see that multiple jobs can be submitted by
the task manager.
It may also be helpful to have a job.template on darwin to use the galton nodes,
we have priority on them.

For now task_manager will only run for 5 minutes (edit task_manager.py (timer) for
different times. I did this to ensure I don't leave it running.

Leaves scripts in ~/.beeflow/worker


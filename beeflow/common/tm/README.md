This is a preliminary Task Manager. It will submit tasks written to a json file.

Example sent_task.json:

```
task_id": 111
name": "GREP"
command": "grep -i database grep.in  > grep.out"
hints": ""
subworkflow": ""
inputs": "{'grep.in'}":wq
```


One way to test the current task manager

```
./clean.sh
python task_manager.py &
./write-tasks-json.sh
```

For now task_manager will only run for 5 minutes (edit task_manager.py (TIMER)


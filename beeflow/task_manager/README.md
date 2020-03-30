# mock task_manager 

task_manager.py uses a verison of Al's by hand grep tasks run one after another
You should copy the job.template to ~/.beeflow/scripts/ and modify as you like
but it will work without the template

for now this is a test to submit and query jobs from the tasks without the graph 
database. To make it work copy the commented copy of wf_interface to beeflow/common

```
cp wf_interface_commented.py ../../beeflow/common/wf_interface.py
```

note: when done checkout wf_interface.py

```
git checkout ../../beeflow/common/wf_interface.py
```



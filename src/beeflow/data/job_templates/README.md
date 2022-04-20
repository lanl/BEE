# Job templates

BEE uses HPC resource scheduler templates to execute tasks on HPC resources. This directory is a home for templates of supported system schedulers. Add the location of your template to the bee.conf file in the TaskManager section.
Example:
```
[task_manager]
...
job_template = $HOME/.config/beeflow/submit.jinja
```

## Jinja2 Templating

The BEE worker code should now work with Jinja2-based templates set with the
`job_template` parameter. An example job template `submit.jinja` is included
here which should work for Slurm.

Currently the template is passed a number of variables which I'll try to
document here:
* `workflow_path` - path for stored workflow info as a string
* `task_name` - task name sring
* `task_id` - task ID string
* `workflow_id` - workflow ID string
* `commands` - list of list of string
* `requirements` - requirements as a dict
* `hints` - hints as a dict
These should be used to determine exactly what options should be generated in
the submission script.

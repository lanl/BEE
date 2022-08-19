# Job templates

BEE uses HPC resource scheduler templates to execute tasks on HPC resources. This directory is a home for templates of supported system schedulers. Add the absolute path to your template to the bee.conf file in the TaskManager section.
Example:
```
[task_manager]
...
job_template = <home dir>/.config/beeflow/submit.jinja
```

## Jinja2 Templating

The BEE worker code should now work with Jinja2-based templates set with the
`job_template` parameter. An example job template `slurm-submit.jinja` is included
here which should work for Slurm.

Currently the template is passed a number of variables which I'll try to
document here:
* `task_save_path` - path for stored task info as a string
* `task_name` - task name sring
* `task_id` - task ID string
* `workflow_id` - workflow ID string
* `env_code` - commands to set environment such as 'module load charliecloud'
* `pre_commands` - initial commands to run before the main command
* `command` - main command to run
* `post_commands` - commands to run after the main command
* `requirements` - requirements as a dict
* `hints` - hints as a dict
These should be used to determine exactly what options should be generated in
the submission script.

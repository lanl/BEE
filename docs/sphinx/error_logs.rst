Information and Error Logs
**************************

BEE components log information and errors in the logs subdirectory of BEE work directory specified in bee.conf as **bee_workdir**. The default location is **$HOME/.beeflow/logs**.There are logs for each component. When you are given a message such as "Check the workflow manager", look for information in the wf_manager.log. The task_manager.log will contain logging information for each step in a workflow including any build logs if a container is built by BEE.

 

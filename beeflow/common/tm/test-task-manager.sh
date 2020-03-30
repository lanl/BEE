#! /bin/bash
# The following are tested:
# (Ignore the error for the job template it creates a simple one.)
# All state changes are printed out.
#
# 1. An unknown task is cancelled but never really existed so the Cancellation fails.
# 2. The grep workflow creates two tasks, the outputs or in grep.out and wc.out 
# 3. Another job is submitted and then cancelled.

# clean up first 

rm *.out
rm *.json
echo "Clean up done, starting tests. "

# run task manager
python task_manager.py &
echo " "

# try to cancel a job that doesn't exist
echo "Cancelling unknown job is correct to fail!"
echo '{' > cancel.json
echo '"task_id": 12345,' >> cancel.json
echo '"name": "unknown",' >> cancel.json
echo '"job_id": 1234' >> cancel.json
echo '}' >> cancel.json

# grep workflow
echo '{ 
"task_id": 111, 
"name": "GREP", 
"command": "grep -i database grep.in  > grep.out",
"hints": {"DockerRequirement": {"DockerImageId": "/usr/projects/beedev/toss-tiny-3-5.tar"}},
"subworkflow": "",
"inputs": "{'grep.in'}",
"outputs": "{'grep.out'}" 
}' > sent_task.json

while [ ! -f "grep.out" ]
do
  sleep 5s
done
echo '{ 
"task_id": 131, 
"name": "WC",
"command": "wc -l grep.out > wc.out",
"hints": {"DockerRequirement": {"DockerImageId": "/usr/projects/beedev/toss-tiny-3-5.tar"}},
"subworkflow": "",
"inputs": "{'grep.out'}",
"outputs": "{'wc.out'}"
}' > sent_task.json

#cancel a job is running

sbatch job-to-cancel.sh
echo "End of test-task-manager.sh, but task_manager and jobs should continue."

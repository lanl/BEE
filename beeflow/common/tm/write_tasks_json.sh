#! /bin/bash

# to test a workflow delete *.out then search for grep.out before adding the json
# for wc also can add ls at the same time as grep
# will need to get task_manager to read more than one task

echo '{ 
"name": "GREP", 
"command": "grep -i database grep.in  > grep.out",
"hints": "", 
"subworkflow": "",
"inputs": "{'grep.in'}",
"outputs": "{'grep.out'}" 
}' > sent_task.json

sleep 5s
echo '{ 
"name": "WC",
"command": "wc -l grep.out > wc.out",
"hints": "",
"subworkflow": "",
"inputs": "{'grep.out'}",
"outputs": "{'wc.out'}"
}' > sent_task.json

sleep 5s
echo '{ 
"name": "LS",
"command": "ls -l",
"hints": "",
"subworkflow": "",
"inputs": "grep.out",
"outputs": "ls.out"
}' > sent_task.json


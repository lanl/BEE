#! /bin/bash

echo '{ 
"task_id": 111, 
"name": "GREP", 
"command": "grep -i database grep.in  > grep.out",
"hints": "", 
"subworkflow": "",
"inputs": "{'grep.in'}",
"outputs": "{'grep.out'}" 
}' > sent_task.json

while [ ! -f "grep.out" ]
do
  sleep 1s
done
echo '{ 
"task_id": 131, 
"name": "WC",
"command": "wc -l grep.out > wc.out",
"hints": "",
"subworkflow": "",
"inputs": "{'grep.out'}",
"outputs": "{'wc.out'}"
}' > sent_task.json

#!/bin/sh
SERVER=http://localhost:5100
URL=/bee_sched/v1/schedule

DATA='{
    "workflow": {
        "name": "workflow-0",
        "levels": [
            [
                {
                    "name": "task-0",
                    "runtime": 10
                }
            ]
        ]
    },
    "clusters": [
        {
            "name": "cluster-0",
            "partitions": [
                {
                    "name": "partition-0"
                }
            ]
        }
    ],
    "start_time": 0
}'
curl -X PUT -H "Content-Type: application/json" --data-raw "$DATA" ${SERVER}${URL}

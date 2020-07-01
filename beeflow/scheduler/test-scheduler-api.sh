#!/bin/sh
#
# Simple tests of the scheduler REST API.
#
SERVER=http://localhost:5100
URL=/bee_sched/v1

# Start the scheduler for testing
python scheduler.py &
SCHEDPID=$!

sleep 1

# Do a PUT request with the JSON data to a URL (method=$1, data=$2, url=$3)
send_json()
{
	local method="$1"
	local data="$2"
	local url="$3"
	curl -X $method -H "Content-Type: application/json" --data-raw \
		"$data" "$url" 2>/dev/null
}

# Test 1
RESOURCES='[
    {
	"name": "resouce-0",
        "cores": 10
    }
]'
TASK_DATA='{
    "task_name": "task-0",
    "runtime": 10,
    "max_cores": 2
}'
echo "#########"
echo "Test 1..."
echo "***Creating resources"
send_json PUT "${CLUSTER_DATA}" "${SERVER}${URL}/resources"
echo "***Scheduling jobs/tasks"
send_json POST "${TASK_DATA}" "${SERVER}${URL}/jobs"
echo "***"
###############################################################################

# Test 2
RESOURCES='[
    {
	"name": "resouce-0",
        "cores": 10
    }
]'
WORKFLOW='{
    "workflow_name": "test-workflow",
    "tasks": {
        "grep": {
            "task_name": "grep",
            "runtime": 10,
            "max_cores": 1
        },
        "wc": {
            "task_name": "wc",
            "runtime": 10,
            "max_cores": 1,
            "depends": ["grep"]
        }
    }
}'


kill ${SCHEDPID}

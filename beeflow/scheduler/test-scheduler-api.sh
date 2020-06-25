#!/bin/sh
#
# Simple tests of the scheduler REST API.
#
SERVER=http://localhost:5100
URL=/bee_sched/v1/schedule

# Start the scheduler for testing
python scheduler.py &
SCHEDPID=$!

sleep 1

# Test 1
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
echo "#########"
echo "Test 1..."
curl -X PUT -H "Content-Type: application/json" --data-raw "$DATA" ${SERVER}${URL}

###############################################################################
# Test 2
DATA='{
    "workflow": {
        "name": "workflow-0",
        "levels": [
            [
                {
                    "name": "task-0",
                    "runtime": 10
                },
                {
                    "name": "task-1",
                    "runtime": 6
                }
            ],
            [
                {
                    "name": "task-2",
                    "runtime": 3
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
echo "#########"
echo "Test 2..."
curl -X PUT -H "Content-Type: application/json" --data-raw "$DATA" ${SERVER}${URL}

###############################################################################
# Test 3
DATA='{
    "workflow": {
        "name": "workflow-0",
        "levels": [
            [
                {
                    "name": "task-0",
                    "runtime": 10
                },
                {
                    "name": "task-1",
                    "runtime": 6
                }
            ],
            [
                {
                    "name": "task-2",
                    "runtime": 3
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
                },
                {
                    "name": "partition-1"
                }
            ]
        }
    ],
    "start_time": 0
}'
echo "#########"
echo "Test 3..."
curl -X PUT -H "Content-Type: application/json" --data-raw "$DATA" ${SERVER}${URL}

###############################################################################
# Test 4
DATA='{
    "workflow": {
        "name": "workflow-0",
        "levels": [
            [
                {
                    "name": "task-0",
                    "runtime": 10
                }
            ],
            [
                {
                    "name": "task-1",
                    "runtime": 10
                }
            ],
            [
                {
                    "name": "task-2",
                    "runtime": 10
                }
            ],
            [
                {
                    "name": "task-3",
                    "runtime": 3
                },
                {
                    "name": "task-4",
                    "runtime": 4
                },
                {
                    "name": "task-5",
                    "runtime": 5
                },
                {
                    "name": "task-6",
                    "runtime": 6
                }
            ]
        ]
    },
    "clusters": [
        {
            "name": "cluster-0",
            "partitions": [
                {
                    "name": "partition-1"
                },
                {
                    "name": "partition-2"
                },
                {
                    "name": "partition-3"
                }
            ]
        }
    ],
    "start_time": 0
}'
echo "#########"
echo "Test 4..."
curl -X PUT -H "Content-Type: application/json" --data-raw "$DATA" ${SERVER}${URL}

###############################################################################
# Test 5
DATA='{
    "workflow": {
        "name": "workflow-0",
        "levels": [
            [
                {
                    "name": "task-0",
                    "runtime": 10
                },
                {
                    "name": "task-1",
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
        },
        {
            "name": "cluster-1",
            "partitions": [
                {
                    "name": "partition-1"
                }
            ]
        }
    ],
    "start_time": 0
}'
echo "#########"
echo "Test 5..."
curl -X PUT -H "Content-Type: application/json" --data-raw "$DATA" ${SERVER}${URL}

###############################################################################
# Test 6 - Test some simple resource needs
DATA='{
    "workflow": {
        "name": "workflow-0",
        "levels": [
            [
                {
                    "name": "task-0",
                    "runtime": 10,
                    "cpus": 2
                }
            ]
        ]
    },
    "clusters": [
        {
            "name": "cluster-0",
            "partitions": [
                {
                    "name": "partition-0",
                    "total_cpus": 1
                },
                {
                    "name": "partition-1",
                    "total_cpus": 2
                }
            ]
        }
    ],
    "start_time": 0
}'
echo "#########"
echo "Test 6..."
curl -X PUT -H "Content-Type: application/json" --data-raw "$DATA" ${SERVER}${URL}

###############################################################################
# Test 7 - Test simple resource need (not satisfied)
DATA='{
    "workflow": {
        "name": "workflow-0",
        "levels": [
            [
                {
                    "name": "task-0",
                    "runtime": 10,
                    "cpus": 64
                }
            ]
        ]
    },
    "clusters": [
        {
            "name": "cluster-0",
            "partitions": [
                {
                    "name": "partition-0",
                    "total_cpus": 1
                },
                {
                    "name": "partition-1",
                    "total_cpus": 2
                }
            ]
        }
    ],
    "start_time": 0
}'
echo "#########"
echo "Test 7..."
curl -X PUT -H "Content-Type: application/json" --data-raw "$DATA" ${SERVER}${URL}

kill ${SCHEDPID}

#! /bin/bash

#This script is temporary for development until we get a REST interface
# it builds a json file for canceling a job that it submits
# run it to test cancelling feature in task monitor

#SBATCH -J cancel-test

echo '{' > cancel.json
echo '"task_id": 11118,' >> cancel.json
echo '"name": "hello",' >> cancel.json
echo '"job_id":' $SLURM_JOBID >> cancel.json
echo '}' >> cancel.json
 
sleep 3m

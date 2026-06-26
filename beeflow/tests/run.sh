#!/bin/bash
#SBATCH --job-name=test_job
#SBATCH --time=00:10:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --error=err.txt
#SBATCH --output=out.txt

echo "Job Running!"

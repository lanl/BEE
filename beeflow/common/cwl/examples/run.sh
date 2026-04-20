#!/bin/bash
#SBATCH --job-name=test_job
#SBATCH --output=${output}
#SBATCH --error=${error}
#SBATCH --time=00:10:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --account=
#SBATCH --partition=
#SBATCH --qos=

module load python

echo "Job started on $(date)"
echo "Running on node(s): $SLURM_NODELIST"
echo "Job ID: $SLURM_JOB_ID"
echo "Job running at $PWD"

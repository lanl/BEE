#!/bin/bash
#SBATCH --job-name=cat-d2457b061c784e70b283789820d6dd3c
#SBATCH --output=/vast/home/szeytun/old-home/szeytun/BEE/BEE-tool/tests/test_workdir/cat.txt
#SBATCH --error=/vast/home/szeytun/old-home/szeytun/BEE/BEE-tool/tests/test_workdir/cat.err
#SBATCH -N 1
#SBATCH -n 1
#SBATCH --open-mode=append
set -e
cd /vast/home/szeytun/old-home/szeytun/BEE/BEE-tool/tests/test_workdir

srun --nodes=1  cat lorem.txt
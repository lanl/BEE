#!/bin/bash
#SBATCH --job-name=cat-1ccaebd659034633807239dc09a56817
#SBATCH --output=/vast/home/szeytun/old-home/szeytun/BEE/BEE-tool/tests/test_workdir/cat.txt
#SBATCH --error=/vast/home/szeytun/old-home/szeytun/BEE/BEE-tool/tests/test_workdir/cat.err
#SBATCH -N 1
#SBATCH -n 1
#SBATCH --open-mode=append
set -e
cd /vast/home/szeytun/old-home/szeytun/BEE/BEE-tool/tests/test_workdir

srun --nodes=1  cat lorem.txt
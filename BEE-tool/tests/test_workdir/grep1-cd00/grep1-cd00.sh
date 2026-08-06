#!/bin/bash
#SBATCH --job-name=grep1-cd00451cce5644689b1f80d485a1ea8e
#SBATCH --output=/vast/home/szeytun/old-home/szeytun/BEE/BEE-tool/tests/test_workdir/occur1.txt
#SBATCH --error=/vast/home/szeytun/old-home/szeytun/BEE/BEE-tool/tests/test_workdir/grep1-cd00/grep1-cd00.err
#SBATCH -N 1
#SBATCH -n 1
#SBATCH --open-mode=append
set -e
cd /vast/home/szeytun/old-home/szeytun/BEE/BEE-tool/tests/test_workdir

srun --nodes=1  grep pulvinar /vast/home/szeytun/old-home/szeytun/BEE/BEE-tool/tests/test_workdir/cat.txt
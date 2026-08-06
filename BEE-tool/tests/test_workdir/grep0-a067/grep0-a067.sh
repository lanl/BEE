#!/bin/bash
#SBATCH --job-name=grep0-a067a938deb74695855d4bfb5ebed50a
#SBATCH --output=/vast/home/szeytun/old-home/szeytun/BEE/BEE-tool/tests/test_workdir/occur0.txt
#SBATCH --error=/vast/home/szeytun/old-home/szeytun/BEE/BEE-tool/tests/test_workdir/grep0-a067/grep0-a067.err
#SBATCH -N 1
#SBATCH -n 1
#SBATCH --open-mode=append
set -e
cd /vast/home/szeytun/old-home/szeytun/BEE/BEE-tool/tests/test_workdir

srun --nodes=1  grep Vivamus /vast/home/szeytun/old-home/szeytun/BEE/BEE-tool/tests/test_workdir/cat.txt
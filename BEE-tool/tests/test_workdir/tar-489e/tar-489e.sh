#!/bin/bash
#SBATCH --job-name=tar-489e226d3d4c49e389671614e9af9263
#SBATCH --output=/vast/home/szeytun/old-home/szeytun/BEE/BEE-tool/tests/test_workdir/tar-489e/tar-489e.out
#SBATCH --error=/vast/home/szeytun/old-home/szeytun/BEE/BEE-tool/tests/test_workdir/tar-489e/tar-489e.err
#SBATCH -N 1
#SBATCH -n 1
#SBATCH --open-mode=append
set -e
cd /vast/home/szeytun/old-home/szeytun/BEE/BEE-tool/tests/test_workdir

srun --nodes=1  tar -cf out.tgz /vast/home/szeytun/old-home/szeytun/BEE/BEE-tool/tests/test_workdir/occur0.txt /vast/home/szeytun/old-home/szeytun/BEE/BEE-tool/tests/test_workdir/occur1.txt
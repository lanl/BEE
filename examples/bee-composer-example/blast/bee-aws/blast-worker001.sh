#!/bin/bash
cd /mnt/docker_share
/home/beeuser/makeflow-examples/blast/blastall -p blastn -d /home/beeuser/makeflow-examples/blast/nt/nt -i small.fasta.0 -o input.fasta.0.out 2> input.fasta.0.err

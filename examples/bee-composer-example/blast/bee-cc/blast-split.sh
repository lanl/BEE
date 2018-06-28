#!/bin/bash
cp /home/beeuser/makeflow-examples/blast/small.fasta /mnt/docker_share/
/home/beeuser/makeflow-examples/blast/split_fasta 100 /mnt/docker_share/small.fasta

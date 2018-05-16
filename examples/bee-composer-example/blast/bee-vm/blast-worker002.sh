#!/bin/bash
cd /mnt/bee_share
/home/beeuser/makeflow-examples/blast/blastall -p blastn -d nt/nt -i small.fasta.1 -o input.fasta.1.out 2> input.fasta.1.err

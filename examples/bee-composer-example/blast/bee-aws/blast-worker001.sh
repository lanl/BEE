#!/bin/bash
cd /mnt/blast
/root/makeflow-examples/blast/blastall -p blastn -d nt/nt -i small.fasta.0 -o input.fasta.0.out 2> input.fasta.0.err

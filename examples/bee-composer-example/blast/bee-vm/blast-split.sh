#!/bin/bash
cp /root/makeflow-examples/blast/small.fasta /mnt/blast/
/root/makeflow-examples/blast/split_fasta 100 /mnt/blast/small.fasta

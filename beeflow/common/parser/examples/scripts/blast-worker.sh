#!/bin/bash
# to run $1 is the worker number 0,1
BLAST_LOC=/home/beeuser/makeflow-examples/blast

cat /mnt/0/split-done.txt
echo "Running worker$1 "

$BLAST_LOC/blastall -p blastn \
    -d $BLAST_LOC/nt/nt -i /mnt/0/small.fasta.$1 -o /mnt/0/input.fasta.$1.out \
	2> /mnt/0/input.fasta.$1.err

echo "blast-worker$1 completed:" > /mnt/0/worker$1-done.txt
date >> /mnt/0/worker$1-done.txt


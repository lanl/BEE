#!/bin/bash

# BEE Charliecloud example utilizing blast
# Argument #1   Blast output/share directory
#               Must remain constant across flow

BLAST_CH=/var/tmp/blast
BLAST_LOC=/home/beeuser/makeflow-examples/blast

if [ -z "$1" ]; then
    BLAST_OUT=~/blast_output2
else
    BLAST_OUT=$1
fi

ch-run --no-home -b $BLAST_OUT $BLAST_CH -- sh -c "$BLAST_LOC/blastall -p blastn \
	-d $BLAST_LOC/nt/nt -i /mnt/0/small.fasta.0 -o /mnt/0/input.fasta.0.out \
	2> /mnt/0/input.fasta.0.err"

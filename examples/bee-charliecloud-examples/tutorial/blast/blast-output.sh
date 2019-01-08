#!/bin/bash

# BEE Charliecloud example utilizing blast
# Argument #1   Blast output/share directory
#               Must remain constant across flow

BLAST_CH=/var/tmp/beelanl.blast
BLAST_LOC=/home/beeuser/makeflow-examples/blast

if [ -z "$1" ]; then
    BLAST_OUT=~/blast_output
else
    BLAST_OUT=$1
fi

ch-run --no-home -b $BLAST_OUT $BLAST_CH -- $BLAST_LOC/cat_blast \
    /mnt/0/output.fasta /mnt/0/input.fasta.0.out /mnt/0/input.fasta.1.out

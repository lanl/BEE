#!/bin/bash

# BEE Charliecloud example utilizing blast
# Argument #1   Blast output/share directory
#               Must remain constant across flow

BLAST_CH=/var/tmp/blast

if [ -z "$1" ]; then
    BLAST_OUT=~/blast_output
else
    BLAST_OUT=$1
fi

ch-run -b $BLAST_OUT $BLAST_CH -- sh -c "cat /mnt/0/input.fasta.0.err \
    /mnt/0/input.fasta.1.err > /mnt/0/output.fasta.err"

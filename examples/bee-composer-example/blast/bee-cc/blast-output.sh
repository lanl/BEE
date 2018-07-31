#!/bin/bash

# BEE Charliecloud example utilizing blast
# Argument #1   Blast output/share directory
#               Must remain constant across flow

BLAST_CH=/var/tmp/blast
BLAST_LOC=/home/beeuser/makeflow-examples/blast

if [ -z "$1" ]; then
    BLAST_OUT=~/blast_output
else
    BLAST_OUT=$1
fi

ch-run --no-home -b $BLAST_OUT $BLAST_CH -- sh - c "$BLAST_LOC/cat_blast \
    output.fasta input.fasta.0.out input.fasta.1.out"
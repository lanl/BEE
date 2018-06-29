#!/bin/bash

# BEE Charliecloud example utilizing blast
# Argument #1   Blast output/share directory
#               Must remain constant across flow

BLAST_CH=/var/tmp/blast

if [ -z "$1" ]; then
    BLAST_OUT=/var/tmp/output
else
    BLAST_OUT=$1
fi

ch-run -b $BLAST_OUT $BLAST_CH -- /blast/cat_blast \
    output.fasta input.fasta.0.out input.fasta.1.out
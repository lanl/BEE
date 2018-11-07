#!/bin/bash

# BEE Charliecloud example utilizing blast
# Argument #1   Blast output/share directory
#               Must remain constant across flow

BLAST_CH=/var/tmp/blast2
BLAST_LOC=/home/beeuser/makeflow-examples/blast

if [ -z "$1" ]; then
    BLAST_OUT=~/blast_output2
else
    BLAST_OUT=$1
fi

rm -rf $BLAST_OUT
mkdir $BLAST_OUT

# Create error files (empty)
touch $BLAST_OUT/input.fasta.0.err \
        $BLAST_OUT/input.fasta.1.err \
        $BLAST_OUT/output.fasta.err

ch-run --no-home -b $BLAST_OUT $BLAST_CH -- sh -c "cp $BLAST_LOC/small.fasta /mnt/0 && \
                                $BLAST_LOC/split_fasta 100 /mnt/0/small.fasta"

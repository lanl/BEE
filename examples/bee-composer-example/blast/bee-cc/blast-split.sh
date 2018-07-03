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

rm -rf $BLAST_OUT
mkdir $BLAST_OUT

# Create error files (empty)
touch $BLAST_OUT/input.fasta.0.err \
        $BLAST_OUT/input.fasta.1.err \
        $BLAST_OUT/output.fasta.err

# Temp solution until Dockerfile can be edited
cp -R /var/tmp/blast/home/beeuser/makeflow-examples/blast /var/tmp/blast/

ch-run -b $BLAST_OUT $BLAST_CH -- cp /blast/small.fasta /mnt/0
ch-run -b $BLAST_OUT $BLAST_CH -- /blast/split_fasta 100 /mnt/0/small.fasta
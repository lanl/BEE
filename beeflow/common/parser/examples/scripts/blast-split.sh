#!/bin/bash


BLAST_LOC=/home/beeuser/makeflow-examples/blast
BLAST_OUT=/mnt/0

touch $BLAST_OUT/input.fasta.0.err \
        $BLAST_OUT/input.fasta.1.err \
        $BLAST_OUT/output.fasta.err
rm $BLAST_OUT/small.fasta*
cp $BLAST_LOC/small.fasta /mnt/0
$BLAST_LOC/split_fasta 100 /mnt/0/small.fasta
echo "blast-split complete:"> /mnt/0/split-done.txt
date >> /mnt/0/split-done.txt

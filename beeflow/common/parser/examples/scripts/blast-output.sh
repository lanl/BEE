#!/bin/bash

BLAST_LOC=/home/beeuser/makeflow-examples/blast


$BLAST_LOC/cat_blast /mnt/0/output.fasta /mnt/0/input.fasta.0.out /mnt/0/input.fasta.1.out

echo "blast-output completed:" > /mnt/0/output-done.txt
date >> /mnt/0/output-done.txt


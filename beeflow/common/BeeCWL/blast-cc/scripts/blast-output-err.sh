#!/bin/bash

BLAST_LOC=/home/beeuser/makeflow-examples/blast

cat /mnt/0/input.fasta.0.err /mnt/0/input.fasta.1.err > /mnt/0/output.fasta.err

echo "blast-output-err completed:" > /mnt/0/output-err-done.txt
date >> /mnt/0/output-err-done.txt


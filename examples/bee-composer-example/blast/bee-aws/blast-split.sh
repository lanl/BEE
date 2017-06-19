#!/bin/bash
#cp /root/makeflow-examples/blast/small.fasta /mnt/blast/
cd /mnt/blast
#wget ftp://ftp.ncbi.nlm.nih.gov/blast/db/nt.44.tar.gz
#mkdir nt
#tar -C nt -xvzf nt.44.tar.gz
/root/makeflow-examples/blast/split_fasta 100 small.fasta

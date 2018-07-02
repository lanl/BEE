FROM beelanl/openmpi_2.0.2

#ENV http_proxy http://proxyout.lanl.gov:8080
#ENV https_proxy http://proxyout.lanl.gov:8080

RUN apt-get update
RUN apt-get -y install gcc g++ make wget git python

USER beeuser

WORKDIR /home/beeuser

RUN git clone https://github.com/cooperative-computing-lab/makeflow-examples.git

WORKDIR /home/beeuser/makeflow-examples/blast


RUN wget ftp://ftp.ncbi.nlm.nih.gov/blast/executables/legacy.NOTSUPPORTED/2.2.26/blast-2.2.26-x64-linux.tar.gz
RUN tar xvzf blast-2.2.26-x64-linux.tar.gz
RUN cp blast-2.2.26/bin/blastall .

RUN wget ftp://ftp.ncbi.nlm.nih.gov/blast/db/nt.44.tar.gz
RUN mkdir nt
RUN tar -C nt -xvzf nt.44.tar.gz
RUN ./makeflow_blast -d nt -i small.fasta -o output.fasta -p blastn --num_seq 10 --makeflow blast.mf

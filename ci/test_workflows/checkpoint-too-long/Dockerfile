# Dummy container with program to run forever
FROM alpine

RUN printf "#!/bin/sh\n" > /usr/bin/checkpoint-program \
 && printf "touch backup0.crx\n" >> /usr/bin/checkpoint-program \
 && printf "sleep 10000000000\n" >> /usr/bin/checkpoint-program \
 && chmod 755 /usr/bin/checkpoint-program

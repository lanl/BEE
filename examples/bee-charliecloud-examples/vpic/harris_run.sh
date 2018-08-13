#!/bin/bash

CH_DIR=/var/tmp/vpic
TSTDIR=/vpic-build/ch-tests/harris

ch-run 	-w \
	--no-home \
	--cd=$TSTDIR \
	$CH_DIR -- ./harris.Linux

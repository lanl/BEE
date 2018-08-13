#!/bin/bash

CH_DIR=/var/tmp/vpic

ch-run 	-w \
	--no-home \
	$CH_DIR -- \
	sh -c "cd vpic-build/ch-tests/lyin_sequoia && ./short_sequoia.Linux"

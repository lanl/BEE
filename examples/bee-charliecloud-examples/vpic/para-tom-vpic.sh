#!/bin/bash

IMG=/var/tmp/vpic
TESTDIR=/vpic-build/ch-tests

ch-run -w --no-home --cd=$TESTDIR/harris $IMG -- ./harris.Linux

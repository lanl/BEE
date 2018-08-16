#!/usr/bin/env bash
mkdir -p output

ch-run --write --no-home --bind=output --cd=/mnt/0 /var/tmp/flecsale -- pwd

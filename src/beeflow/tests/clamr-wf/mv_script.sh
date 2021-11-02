#!/usr/bin/env bash
# One argument is given: the absolute path to the
# CLAMR output directory (graphics output)
set -e

CLAMR_OUTDIR="$1"
CLAMR_BASEDIR=$(basename "$1")
CLAMR_TMPDIR=$(mktemp -d clamr.XXXXX -p /tmp)

mv "$CLAMR_OUTDIR" "$CLAMR_TMPDIR"
echo "{\"stdout\": \"${CLAMR_TMPDIR}/${CLAMR_BASEDIR}/graph%05d.png\"}"

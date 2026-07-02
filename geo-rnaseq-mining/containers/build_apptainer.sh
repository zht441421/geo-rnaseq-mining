#!/usr/bin/env bash
set -euo pipefail

apptainer build geo-rnaseq-mining.sif containers/apptainer.def

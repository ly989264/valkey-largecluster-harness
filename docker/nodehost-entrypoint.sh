#!/bin/sh
set -eu

cd /data/valkey-largecluster
exec python3 -m nodehost.nodehostctl "$@"

#!/bin/sh
set -eu

cd /data/valkey-largecluster

if [ "${1:-}" = "start" ]; then
  run_dir=""
  previous=""
  for arg in "$@"; do
    if [ "$previous" = "--run-dir" ]; then
      run_dir="$arg"
      previous=""
      continue
    fi
    previous="$arg"
  done

  python3 -m nodehost.nodehostctl "$@"

  if [ -n "$run_dir" ]; then
    trap 'python3 -m nodehost.nodehostctl stop --run-dir "$run_dir"; exit 0' INT TERM
  fi
  while :; do
    sleep 3600 &
    wait $!
  done
fi

exec python3 -m nodehost.nodehostctl "$@"

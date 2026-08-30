#!/usr/bin/env sh
set -eu

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
lab_dir=$(CDPATH= cd -- "$script_dir/.." && pwd)

docker build --pull --tag orr-frr:10.7.0 "$lab_dir/docker"

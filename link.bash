#!/bin/bash
set -ueo pipefail

app_path="$(cd "$(dirname "$0")"; pwd)"

bin_path="/usr/local/bin/bsr"
if [[ -n "${BSR_BIN_PATH-}" ]]; then
	bin_path="$BSR_BIN_PATH"
fi

ln -s "$app_path/src/main.py" "$bin_path"


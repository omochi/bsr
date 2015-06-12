#!/bin/bash
set -ueo pipefail

install_path="/usr/local/lib/bsr"
bin_path="/usr/local/bin/bsr"

install_dir_name="$(basename "$install_path")"

cd "$(dirname "$install_path")"
git clone "https://github.com/omochi/bsr.git" "$install_dir_name"
cd "$install_dir_name"

export BSR_BIN_PATH="$bin_path"
./link.bash

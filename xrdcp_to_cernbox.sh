#!/usr/bin/env bash

readonly PROGDIR="$(readlink -m $(dirname $0))"
readonly INPUT="$PROGDIR/some_src_dir"
readonly OUTDIR="/eos/user/some/user/dir/"


set_voms_proxy() {
  # If the environment variable X509_USER_PROXY is unset or empty,
  # request a new VOMS-proxy and export it as that variable.
  if [ -z "$X509_USER_PROXY" ]; then
    local proxy_path="$PROGDIR/x509up_$UID"
    voms-proxy-init -voms cms -out "$proxy_path"
    export X509_USER_PROXY="$proxy_path"
  fi
}


xrdcp_wrapper() {
  local logical_filename="$1"
  local outdir="$2"
  local basename="${logical_filename##*/}"
  local src="root://xrootd-cms.infn.it//$logical_filename"
  local dst="root://eosuser.cern.ch//$outdir/$basename"
  xrdcp --posc --silent "$src" "$dst"
}


main() {
  # Setup the VOMS-proxy for XRootD access.
  set_voms_proxy
  # Create the output directory.
  eos root://eosuser.cern.ch mkdir -p "$OUTDIR"
  # Count the total number of files to be copied.
  local num_total="$(cat $INPUT | wc -l)"
  # Copy files in parallel, retrying until all have been copied.
  export -f xrdcp_wrapper
  local num_copied=0
  local counter=1
  while [ $num_copied -lt $num_total ]; do
    echo "Starting copy attempt #$counter"
    parallel --max-procs 8 --timeout 120 xrdcp_wrapper {} "$OUTDIR" <<< "$(cat $INPUT)"
	num_copied="$(eos root://eosuser.cern.ch ls "$OUTDIR" | wc -l)"
	echo "$num_copied/$num_total files copied"
	(( counter++ ))
  done
}
main


#!/usr/bin/env bash

#-------------------------------------------------
# User-Configurable
readonly QUERY="dataset=/*/*VHBB_HEPPY_V24*/USER instance=prod/phys03"
#-------------------------------------------------
readonly PROGDIR="$(readlink -m $(dirname $0))"
readonly OUTDIR="$PROGDIR/datasetsblah"


set_voms_proxy() {
  # If the environment variable X509_USER_PROXY is unset or empty,
  # request a new VOMS-proxy and export it as that variable.
  if [ -z "$X509_USER_PROXY" ]; then
    local proxy_path="$PROGDIR/x509up_$UID"
	voms-proxy-init -voms cms -out "$proxy_path"
	export X509_USER_PROXY="$proxy_path"
  fi
}


generate_file_list() {
  # Store the filenames of a dataset in a file named after its processed dataset.
  local full_dataset_name="$1"
  local outdir="$2"
  local processed_dataset_name="$(expr "$full_dataset_name" : '\/.*\/\(.*\)\/.*')"
  das_client.py --query="file dataset="$full_dataset_name" instance=prod/phys03" --limit=0 > "$outdir/$processed_dataset_name"
}


main() {
  # Set the VOMS-proxy used by das_client.py to authenticate with CMSWEB.
  set_voms_proxy
  # Export the function for use with GNU parallel.
  export -f generate_file_list
  # Find all datasets matching the query.
  local full_dataset_names="$(das_client.py --query="$QUERY" --limit=0)"
  echo "Found "$(wc -l <<< "$full_dataset_names")" datasets. Generating file lists..."
  # Generate file lists for all matching datasets.
  parallel --bar --max-procs 8 generate_file_list {} "$OUTDIR" <<< "$full_dataset_names"
}
main


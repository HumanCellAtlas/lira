#!/usr/bin/env bash

query_json=$1
source config.sh
./subscription-create.py "$dss_url?replica=gcp" $green_url $listener_secret $key_file $query_json

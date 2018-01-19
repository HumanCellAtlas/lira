#!/usr/bin/env bash

dss_url=$1
green_url=$2
key_file=$3
listener_secret=$4
query_json=$5

./subscription-create.py "$dss_url?replica=gcp" $green_url $listener_secret $key_file $query_json

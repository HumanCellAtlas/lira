#!/usr/bin/env bash

dss_url=$1
green_url=$2
key_file=$3
listener_secret=$4
query_json=$5
hmac_key_id=$6
additional_metadata=$7

if [ -z $dss_url ]; then
  echo "dss_url is required"
  error=1
fi
if [ -z $green_url ]; then
  echo "green_url is required"
  error=1
fi
if [ -z $key_file ]; then
  echo "key_file is required"
  error=1
fi
if [ -z $listener_secret ]; then
  echo "listener_secret is required"
  error=1
fi
if [ -z $query_json ]; then
  echo "query_json is required"
  error=1
fi

if [ "$error" == "1" ]; then
  echo -e "Usage: bash subscription-create.sh dss_url green_url key_file listener_secret query_json [hmac_key_id] [additional_metadata]\n"
  exit 1
fi

if [ -n "$hmac_key_id" ]; then
  auth_args="-hmac_key_id $hmac_key_id -hmac_key $listener_secret"
else
  auth_args="-query_param_token $listener_secret"
fi

if [ $additional_metadata ]; then
    additional_metadata_flag="--additional_metadata"
fi

./subscription-create.py \
  -dss_url "$dss_url?replica=gcp" \
  -callback_base_url $green_url \
  -key_file $key_file \
  -query_json $query_json \
  $(echo "$auth_args" | xargs) \
  $additional_metadata_flag $additional_metadata

#!/usr/bin/env bash

# Usage: bash subscription-create.sh config.sh query_json [additional_metadata]

config_script=$1
query_json=$2
additional_metadata=$3

source $config_script

if [ -n "$hmac_key_id" ]; then
  auth_args="--hmac_key_id=$hmac_key_id --hmac_key=$lira_secret"
else
  auth_args="--query_param_token=$lira_secret"
fi

if [ $additional_metadata ]; then
    additional_metadata_flag="--additional_metadata="
fi

python3 subscribe.py create --dss_url="$dss_url" \
                            --key_file="$key_file" \
                            --google_project="$google_project" \
                            --replica="$replica" \
                            --callback_base_url="$lira_url" \
                            --query_json="$query_json" \
                            $(echo "$auth_args" | xargs) \
                            "$additional_metadata_flag""$additional_metadata"

#!/usr/bin/env bash

# Usage: bash subscription-delete.sh config.sh subscription_id

config_script=$1
subscription_id=$2

source $config_script
python3 subscribe.py delete --dss_url="$dss_url" \
                            --key_file="$key_file" \
                            --google_project="$google_project" \
                            --replica="$replica" \
                            --subscription_id="$subscription_id"

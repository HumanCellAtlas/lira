#!/usr/bin/env bash

# Usage: bash subscriptions-list.sh config.sh

config_script=$1

source $config_script
python3 subscribe.py list --dss_url="$dss_url" \
                          --key_file="$key_file" \
                          --google_project="$google_project" \
                          --replica="$replica"

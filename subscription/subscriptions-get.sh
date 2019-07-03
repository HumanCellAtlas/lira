#!/usr/bin/env bash

# Usage: bash subscriptions-get.sh config.sh

script_config=$1

source $script_config
python3 subscribe.py get --dss_url="$dss_url" \
                         --key_file="$key_file" \
                         --google_project="$google_project" \
                         --subscription_type="jmespath" \
                         --replica="$replica"

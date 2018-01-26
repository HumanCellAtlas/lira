#!/usr/bin/env bash

config_file=$1

if [ -z $config_file ]; then
    echo -e "\nYou must provide a config file."
    echo -e "\nUsage: bash populate_listener_config_secret.sh /path/to/config.json\n"
    exit 1
fi

kubectl create secret generic \
    listener-config-$(date '+%Y-%m-%d-%H-%M') \
    --from-file=config=$config_file \

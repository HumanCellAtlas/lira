#!/usr/bin/env bash

config_file=$1

if [ -z $config_file ]; then
    echo -e "\nYou must provide a config file."
    echo -e "\nUsage: bash populate_listener_config_secret.sh /path/to/config.json\n"
    exit 1
fi

config_secret_name=listener-config-$(date '+%Y-%m-%d-%H-%M')
echo $config_secret_name

kubectl create secret generic \
    $config_secret_name \
    --from-file=config=$config_file \

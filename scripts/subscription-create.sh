#!/usr/bin/env bash

source config.sh
./subscription-create.py "$dss_url?replica=aws" $green_url $listener_secret $key_file

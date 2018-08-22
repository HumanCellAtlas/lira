#!/usr/bin/env bash

uuid=$1
source config.sh
./subscription-delete.py "$dss_url/$uuid?replica=gcp" $key_file
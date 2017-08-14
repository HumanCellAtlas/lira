#!/usr/bin/env bash

uuid=$1
source config.sh
./subscription-delete.py "$dss_url/$uuid?replica=aws" $key_file

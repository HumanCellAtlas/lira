#!/usr/bin/env bash

source config.sh
./subscription-create.py "$dss_url?replica=aws" $green_url $oauth_token $listener_secret

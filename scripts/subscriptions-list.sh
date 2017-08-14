#!/usr/bin/env bash

source config.sh
./subscriptions-list.py "$dss_url?replica=aws"

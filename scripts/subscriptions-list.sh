#!/usr/bin/env bash

source config.sh
curl -H "Authorization: Bearer $oauth_token" "$dss_url?replica=aws"


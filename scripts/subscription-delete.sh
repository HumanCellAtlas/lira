#!/usr/bin/env bash

uuid=$1
source config.sh
curl -H "Authorization: Bearer $oauth_token" "$dss_url?uuid=$uuid&replica=aws"


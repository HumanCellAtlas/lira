#!/usr/bin/env bash

uuid=$1
source config.sh
curl -X DELETE -H "Authorization: Bearer $oauth_token" "$dss_url/$uuid?replica=aws"


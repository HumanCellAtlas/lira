#!/usr/bin/env bash

secret_name=$1
cert_dir=$2

kubectl create secret tls $secret_name-$(date '+%Y-%m-%d') \
  --cert=$cert_dir/fullchain.pem \
  --key=$cert_dir/privkey.pem

echo $secret_name-$(date '+%Y-%m-%d')
#!/usr/bin/env bash

kubectl create secret tls hca-tls-secret \
  --cert=/etc/secondary-analysis/fullchain.pem \
  --key=/etc/secondary-analysis/privkey.pem

#!/usr/bin/env bash

kubectl create secret generic listener-config-$(date '+%Y-%m-%d-%H-%M-%S') \
--from-file=config=/etc/secondary-analysis/config.json \
--from-file=bucket-reader-key=/etc/secondary-analysis/bucket-reader-key.json

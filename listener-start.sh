#!/usr/bin/env bash

gcloud config set project broad-dsde-mint-dev
gcloud auth activate-service-account --key-file=/etc/secondary-analysis/bucket-reader-key.json

python green-box-api.py

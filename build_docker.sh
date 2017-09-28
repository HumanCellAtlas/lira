#!/usr/bin/env bash

env=$1
tag=$2
docker build -t gcr.io/broad-dsde-mint-$env/listener:$tag .

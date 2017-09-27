#!/usr/bin/env bash
env=$1
tag=$2
docker run -e listener_config=/etc/secondary-analysis/config.json -v /private/etc/secondary-analysis:/etc/secondary-analysis:ro --publish 8080:8080 --name green -t gcr.io/broad-dsde-mint-${env}/listener:$tag
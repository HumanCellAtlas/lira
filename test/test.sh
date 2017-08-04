#!/usr/bin/env bash

touch test_key.json
docker build -t gcr.io/broad-dsde-mint-dev/green-node:test .

docker run gcr.io/broad-dsde-mint-dev/green-node:test bash -c "cd test && python -m unittest -v test_service"

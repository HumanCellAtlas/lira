#!/usr/bin/env bash

docker build -t gcr.io/broad-dsde-mint-dev/lira:test ../..

# Run unit tests in docker container
docker run -e listener_config=config.json gcr.io/broad-dsde-mint-dev/lira:test bash -c "python -m unittest discover -v"

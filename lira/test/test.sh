#!/usr/bin/env bash

docker build -t lira:test ../..

# Run unit tests in docker container
docker run -e lira_config=config.json --entrypoint python3 lira:test -m unittest discover -v

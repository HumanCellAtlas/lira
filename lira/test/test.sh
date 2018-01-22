#!/usr/bin/env bash

docker build -t lira:test ../..

# Run unit tests in docker container
docker run -e listener_config=config.json lira:test bash -c "python -m unittest discover -v"

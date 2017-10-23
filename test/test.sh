#!/usr/bin/env bash

touch test_key.json
docker build -t gcr.io/broad-dsde-mint-dev/listener:test ..

# Tell Jenkins to run both unittests in root folder and listener_utils package folder
docker run -e listener_config=config.json gcr.io/broad-dsde-mint-dev/listener:test bash -c "python -m unittest discover -v && cd test && python -m unittest discover -v"

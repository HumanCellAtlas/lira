#!/usr/bin/env bash

touch test_key.json
docker build -t gcr.io/broad-dsde-mint-dev/listener:test ..

docker run -e listener_config=config.json gcr.io/broad-dsde-mint-dev/listener:test bash -c "cd test && python -m unittest -v test_service test_validate_config"

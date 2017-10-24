#!/usr/bin/env bash


# Set and check parameters
env=$1
tag=$2
if [ -z "$env" ] || [ -z "$tag" ]; then
    echo "Must pass in tag and env to be used for building and running docker image! e.g. test.sh dev test"
    exit 1
fi


# Change directory to build dockerfile
cd ../../

docker build -t gcr.io/broad-dsde-mint-$env/listener:$tag .

# Change back directory
cd -

docker run -e listener_config=test_data/config.json gcr.io/broad-dsde-mint-$env/listener:$tag bash -c "python -m unittest discover -v"

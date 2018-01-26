#!/usr/bin/env bash
tag=$1
config=$2
port=$3

if [ -z $tag ]; then
    echo -e "\nYou must specify a tag"
    error=1
elif [ -z $config ]; then
    echo -e "\nYou must specify a config file"
    error=1
elif [ -z $port ]; then
    port=8080
fi

if [ $error -eq 1 ]; then
    echo -e "\nUsage: bash run_docker.sh TAG /absolute/path/to/config.json [PORT]\n"
    exit 1
fi

# Location in docker container where config file will be copied 
mounted_config=/etc/secondary-analysis/config.json

echo -e "\nRemoving any previously started lira containers\n"
docker stop lira
docker rm lira
echo ""

docker run \
    --name lira \
    --publish $port:$port \
    -v $config:$mounted_config:ro \
    -e listener_config=$mounted_config \
    lira:$tag \
    $port

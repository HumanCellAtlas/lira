#!/usr/bin/env bash
tag=$1
config=$2
caas_key=$3
port=$4


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
    1>&2 echo
    1>&2 echo "Usage: bash run_docker.sh TAG CONFIG [CAAS_KEY [PORT]]"
    1>&2 echo
    1>&2 echo "Where: CONFIG is the absolute path to a Lira config file in JSON."
    1>&2 echo "       TAG is the docker image tag."
    1>&2 echo "       CAAS_KEY is a JSON key file for Cromwell As A Service."
    1>&2 echo "       PORT is a port number to bind (default 8080)."
    1>&2 echo
    exit 1
fi

# Location in docker container where config file will be copied
mounted_config=/etc/secondary-analysis/config.json

# Location in docker container where the caas key will be copied
mounted_caas_key=/etc/secondary-analysis/caas_key.json

echo -e "\nRemoving any previously started lira containers\n"
docker stop lira
docker rm lira
echo ""

if [ $caas_key ]; then
    docker run \
        --name lira \
        --publish $port:$port \
        -v $config:$mounted_config:ro \
        -v $caas_key:$mounted_caas_key:ro \
        -e lira_config=$mounted_config \
        -e caas_key=$mounted_caas_key \
        lira:$tag \
        $port
else
    docker run \
        --name lira \
        --publish $port:$port \
        -v $config:$mounted_config:ro \
        -e lira_config=$mounted_config \
        lira:$tag \
        $port
fi

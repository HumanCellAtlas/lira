#!/usr/bin/env bash

declare -r tag=$1

if [ -z "$tag" ]; then
    1>&2 echo
    1>&2 echo "You must provide a tag"
    1>&2 echo
    1>&2 echo "Usage: bash build_docker.sh TAG"
    1>&2 echo
    exit 1
fi

docker build -t "lira:$tag" .

#!/usr/bin/env bash

set -e -o pipefail

# Exit 1 unless arguments in "$@" are a valid command line.
#
is_usage_ok () {
    local -r tag=$1 config=$2 port=$3
    if [ "$tag" ] && [[ $port =~ ^[0-9]+$ ]] && jq . "$config" >/dev/null
    then
        : OK
    else
        1>&2 echo
        1>&2 echo "Usage: bash run_docker.sh TAG CONFIG [PORT]"
        1>&2 echo
        1>&2 echo "Where: CONFIG is the absolute path to a Lira config file."
        1>&2 echo "       TAG is the docker image tag."
        1>&2 echo "       PORT is a port number to bind (default 8080)."
        1>&2 echo
        1>&2 echo "NOTE:  CONFIG is a JSON file."
        1>&2 echo
        exit 1
    fi
}

# Run "$@" as a docker command line.
#
run_it () {
    1>&2 echo
    1>&2 echo Removing any previously started lira containers.
    1>&2 echo
    1>&2 echo Running: docker stop lira
    docker stop lira || true
    1>&2 echo Running: docker rm lira
    docker rm lira || true
    1>&2 echo
    1>&2 echo Run '"docker stop lira"' in another shell session
    1>&2 echo to shut the lira container down.
    1>&2 echo
    1>&2 echo Running: docker "$@"
    docker "$@"
}

main () {
    local -r wd=$(pwd) tag=$1 config=$2 port=${3:-8080}
    is_usage_ok "$tag" "$config" "$port"
    local -r tmpdir=$(mktemp -d "$wd/${0##*/}XXXXXX")
    trap "rm -rf ${tmpdir}" ERR EXIT HUP INT TERM
    local -r lira=/etc/secondary-analysis/lira
    local cmd=(run --name lira --publish "$port:$port"
               --volume "$tmpdir:$lira:ro"
               -e "lira_config=$lira/config.json")
    cp "$config" "$tmpdir/config.json"
    if jq --exit-status .use_caas "$config" > /dev/null; then
        vault read --format=json --field=data \
              secret/dsde/mint/test/lira/caas-prod-key.json \
              > "$tmpdir/caas_key.json"
        cmd+=(-e "caas_key=$lira/caas_key.json")
    fi
    cmd+=("lira:$tag" "$port")
    run_it "${cmd[@]}"
}

main "$@"

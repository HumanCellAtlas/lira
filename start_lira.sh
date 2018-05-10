#!/usr/bin/env bash

port=$1

echo -e "\nStarting Lira\n"

if [ -z $port ]; then
    echo "Using default port 8080"
    echo -e "To change port, start this way: bash start_lira.sh PORT\n"
    port=8080
fi

# Having too small number for the timeout argument can cause Gunicorn run into CRITICAL worker timeout problems
gunicorn lira.lira:app -b 0.0.0.0:$port --timeout 120

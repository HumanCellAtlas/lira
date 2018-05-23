#!/usr/bin/env bash

port=$1

echo -e "\nStarting Lira\n"

if [ -z $port ]; then
    echo "Using default port 8080"
    echo -e "To change port, start this way: bash start_lira.sh PORT\n"
    port=8080
fi

#--workers: by default, it's set to 1, which is not enough, especially with sync workers, which means any of long
#   requests will break/block the main process and cause CRITICAL TIMEOUTS problems.
#   Now it's set to 2*AVAILABLE_CPU_CORES_OF_THE_CURRENT_MACHINE + 1, according to the suggestion of the gunicorn doc.
#--timeout: by default, it's set to 30s, which is not enough for some of the requests that are sent to Cromwell.
#   It's set to 60 seconds now, which is consistent with the response timeout(NOT the health check timeout) of
#   our GKE Load Balancer.
#--graceful-timeout: by default, it's set to 30s, this parameter helps the workers reboot gracefully,
#   instead of shutting down immediately. It's set to 60s now to be consistent with the timeouts.
#--worker-class: this is the critical parameter that controls the working pattern of gunicorn server.
#   According to its doc, we should use async workers so that those time-consuming requests won't block the worker.
#   It's set to gevent now, since the other async choice for us, gthread workers, are suitable for CPU bound tasks,
#   instead of I/O bound tasks in our case.
gunicorn lira.lira:app -b 0.0.0.0:$port \
    --workers $((2 * $(getconf _NPROCESSORS_ONLN) + 1)) \
    --timeout 60 \
    --graceful-timeout 60 \
    --worker-class gevent

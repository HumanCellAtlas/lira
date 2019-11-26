#!/usr/bin/env bash

port=$1

echo -e "\nStarting Lira\n"

if [ -z "${port}" ]; then
    echo "Using default port 8080"
    echo -e "To change port, start this way: bash start_lira.sh PORT\n"
    port=8080
fi

#--workers: by default, it's set to 1, which is not enough, especially with sync workers, which means any of long
#   requests will break/block the main process and cause CRITICAL TIMEOUTS problems.
#   The command will try to get the (2 * current number of CPU cores) + 1 first, if it failed, it will use 5 as the
#   the number of workers, for portability purposes.
#--timeout: by default, it's set to 30s, which is not enough for some of the requests that are sent to Cromwell or the
#   HCA Data Store. It's set to 180 seconds now, which is consistent with the response timeout(NOT the health check timeout) of
#   our GKE Load Balancer.
#--graceful-timeout: by default, it's set to 30s, this parameter helps the workers reboot gracefully,
#   instead of shutting down immediately. It's set to 180s now to be consistent with the timeouts.
#--worker-class: this is the critical parameter that controls the working pattern of gunicorn server.
#   According to its doc, we should use async workers so that those time-consuming requests won't block the worker.
#   It's set to gevent now, since the other async choice for us, gthread workers, are suitable for CPU bound tasks,
#   instead of I/O bound tasks in our case.
gunicorn lira.lira:app -b 0.0.0.0:"${port}" \
    --workers $((2 * $(getconf _NPROCESSORS_ONLN 2>/dev/null || getconf NPROCESSORS_ONLN 2>/dev/null || echo 2) + 1)) \
    --timeout 180 \
    --graceful-timeout 180 \
    --worker-class sync

#!/usr/bin/env bash

# Creates a sink for exporting logs from Stackdriver.
# Lira logs get sent to Stackdriver when running in Google Cloud Platform.
# Creating the sink allows the logs to be exported automatically to a
# Google Pub/Sub topic that feeds them into the DCP's central logging infrastructure.

# Parameters

# SINK_NAME
# An arbitrary identifier that serves to uniquely identify
# a logging export sink within a Google Cloud Project (there could be several in a project).

# DESTINATION
# This tells Google where to send the logs.
# Several kinds of destinations are supported by Google, but for integration with
# DCP centralized logging, this must point to the Pub/Sub topic that the central
# logging system is monitoring, of the form
# pubsub.googleapis.com/projects/<logs_project_id>/topics/<topic_name>
# logs_project_id and topic_name can be obtained from the DCP logging system administrator.

SINK_NAME=${SINK_NAME:-""}
DESTINATION=${DESTINATION:-""}

ERROR=0
if [ -z "${SINK_NAME}" ]; then
  printf "\nYou must provide a sink name\n"
  ERROR=1
fi
if [ -z "${DESTINATION}" ]; then
  printf "\nYou must provide a DESTINATION\n"
  ERROR=1
fi
if [ "${ERROR}" -eq 1 ]; then
  printf "\nUsage: bash create-logging-sink.sh SINK_NAME DESTINATION\n\n"
  exit 1
fi

printf "\nCreating log sink\n"
gcloud -q logging sinks create "${SINK_NAME}" "${DESTINATION}"

printf "\nGetting email address associated with sink:\n"
LOG_EMAIL=$(gcloud logging sinks describe "${SINK_NAME}" | grep writerIdentity | sed 's/writerIdentity:\ serviceAccount:\(.*\)/\1/g')

printf "Please register this email address: %s with an Administrator of DCP central logging.\n" "${LOG_EMAIL}"

#!/usr/bin/env bash

# Creates a sink for exporting logs from Stackdriver.
# Lira logs get sent to Stackdriver when running in Google Cloud Platform.
# Creating the sink allows the logs to be exported automatically to a
# Google Pub/Sub topic that feeds them into the DCP's central logging infrastructure.

# Parameters

# sink_name
# An arbitrary identifier that serves to uniquely identify
# a logging export sink within a Google Cloud Project (there could be several in a project).

# destination
# This tells Google where to send the logs.
# Several kinds of destinations are supported by Google, but for integration with
# DCP centralized logging, this must point to the Pub/Sub topic that the central
# logging system is monitoring, of the form
# pubsub.googleapis.com/projects/<logs_project_id>/topics/<topic_name>
# logs_project_id and topic_name can be obtained from the DCP logging system administrator.

sink_name=$1
destination=$2

error=0
if [ -z $sink_name ]; then
  printf "\nYou must provide a sink name\n"
  error=1
fi
if [ -z $destination ]; then
  printf "\nYou must provide a destination\n"
  error=1
fi
if [ $error -eq 1 ]; then
  printf "\nUsage: bash create-logging-sink.sh SINK_NAME DESTINATION\n\n"
  exit 1
fi

printf "\nCreating log sink\n"
gcloud -q logging sinks create $sink_name $destination

printf "\nGetting email address associated with sink:\n"
log_email=$(gcloud logging sinks describe $sink_name | grep writerIdentity | sed 's/writerIdentity:\ serviceAccount:\(.*\)/\1/g')

printf "$log_email"
printf "\n\nYou should send the above email address to an administrator of DCP central logging for registration.\n\n"

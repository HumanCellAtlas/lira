#!/usr/bin/env bash

# Create listener cluster
gcloud container clusters create listener

# Create deployment
kubectl create -f listener-deployment.yaml --record

# Create service
kubectl create -f listener-service.yaml --record

# Create static ip address
gcloud compute addresses create listener --global

# Create ingress
kubectl create -f listener-ingress.yaml --record

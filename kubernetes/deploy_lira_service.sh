#!/usr/bin/env bash

# Variables
GCLOUD_PROJECT=${GCLOUD_PROJECT:-"broad-dsde-mint-dev"} # other envs - broad-dsde-mint-test, broad-dsde-mint-staging, hca-dcp-pipelines-prod

KUBERNETES_NAMESPACE=${KUBERNETES_NAMESPACE:-"green-100-us-central1-ns"}
KUBERNETES_CLUSTER=${KUBERNETES_CLUSTER:-"green-100-us-central1"}
KUBERNETES_ZONE=${KUBERNETES_ZONE:-"us-central1-a"}
TLS_SECRET_NAME="${TLS_SECRET_NAME:-""}-$(date '+%Y-%m-%d')"
VAULT_TOKEN_PATH=${VAULT_TOKEN_PATH:-"${HOME}/.vault-token"}
APPLICATION_NAME=${APPLICATION_NAME:-"lira"}
SERVICE_NAME=${SERVICE_NAME:-"lira-service"}

echo "Getting kubernetes context"
gcloud container clusters get-credentials "${KUBERNETES_CLUSTER}" \
                 --zone "${KUBERNETES_ZONE}" \
                 --project "${GCLOUD_PROJECT}"

echo "Generating service file"
docker run -i --rm -e APPLICATION_NAME="${APPLICATION_NAME}" \
                   -e SERVICE_NAME="${SERVICE_NAME}" \
                   -v "${VAULT_TOKEN_PATH}":/root/.vault-token \
                   -v "${PWD}":/working \
                   broadinstitute/dsde-toolbox:ra_rendering \
                   /usr/local/bin/render-ctmpls.sh \
                   -k /working/lira-service.yaml.ctmpl

echo "Deploying Lira Service"
kubectl apply -f lira-service.yaml \
              --record \
              --namespace="${KUBERNETES_NAMESPACE}"

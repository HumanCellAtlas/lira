#!/usr/bin/env bash

# Variables
GCLOUD_PROJECT=${GCLOUD_PROJECT:-"broad-dsde-mint-dev"} # other envs - broad-dsde-mint-test, broad-dsde-mint-staging, hca-dcp-pipelines-prod
KUBERNETES_NAMESPACE=${KUBERNETES_NAMESPACE:-"green-100-us-central1-ns"}
KUBERNETES_CLUSTER=${KUBERNETES_CLUSTER:-"green-100-us-central1"}
KUBERNETES_ZONE=${KUBERNETES_ZONE:-"us-central1-a"}
LIRA_ENVIRONMENT=${LIRA_ENVIRONMENT:-""}
CAAS_ENVIRONMENT=${CAAS_ENVIRONMENT:-"caas-prod"}
VAULT_TOKEN_PATH=${VAULT_TOKEN_PATH:-"/etc/vault-token-dsde"}

APPLICATION_NAME="lira"
SERVICE_NAME="lira-service"

CAAS_KEY_PATH="secret/dsde/mint/${LIRA_ENVIRONMENT}/${APPLICATION_NAME}/${CAAS_ENVIRONMENT}-key.json"
CAAS_KEY_FILE="${CAAS_ENVIRONMENT}-key.json"

echo "Retrieving service account key"
docker run -i --rm \
               -v "${VAULT_TOKEN_PATH}":/root/.vault-token \
               -v "${PWD}":/working broadinstitute/dsde-toolbox:ra_rendering \
               vault read -format=json "${CAAS_KEY_PATH}" | jq .data > "${CAAS_KEY_FILE}"

echo "Authenticating with the service account"
gcloud auth activate-service-account --key-file "${CAAS_KEY_FILE}"


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

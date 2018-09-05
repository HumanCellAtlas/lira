#!/usr/bin/env bash

# Variables
LIRA_ENVIRONMENT=${LIRA_ENVIRONMENT:-""} # other valid envs: test, staging, prod
GCLOUD_PROJECT=${GCLOUD_PROJECT:-"broad-dsde-mint-dev"} # other envs - broad-dsde-mint-test, broad-dsde-mint-staging, hca-dcp-pipelines-prod
GENERATE_CERTS=${GENERATE_CERTS:-"true"}


KUBERNETES_NAMESPACE=${KUBERNETES_NAMESPACE:-"green-100-us-central1-ns"}
KUBERNETES_CLUSTER=${KUBERNETES_CLUSTER:-"green-100-us-central1"}
KUBERNETES_ZONE=${KUBERNETES_ZONE:-"us-central1-a"}

CAAS_ENVIRONMENT=${CAAS_ENVIRONMENT:-"caas-prod"}
VAULT_TOKEN_PATH=${VAULT_TOKEN_PATH:-"/etc/vault-token-dsde"}

APPLICATION_NAME="lira"
GLOBAL_IP_NAME="lira"
INGRESS_NAME="lira-ingress"
SERVICE_NAME="lira-service"
TLS_FULL_CHAIN_DIR="lira-ssl-certificate.crt"
TLS_PRIVATE_KEY_DIR="lira-ssl-certificate.key"
TLS_SECRET_NAME="hca-tls-secret"-$(date '+%Y-%m-%d-%H-%M-%S')

CAAS_KEY_FILE="${CAAS_ENVIRONMENT}-key.json"
CAAS_KEY_PATH="secret/dsde/mint/${LIRA_ENVIRONMENT}/${APPLICATION_NAME}/${CAAS_KEY_FILE}"

echo "Retrieving service account key"
docker run -i --rm \
               -v "${VAULT_TOKEN_PATH}":/root/.vault-token \
               -v "${PWD}":/working broadinstitute/dsde-toolbox:ra_rendering \
               vault read -format=json "${CAAS_KEY_PATH}" | jq .data > "${CAAS_KEY_FILE}"

echo "Authenticating with the service account"
gcloud auth activate-service-account --key-file "${CAAS_KEY_FILE}"

if [ ${GENERATE_CERTS} == "true" ];
then
    ./get_certs.sh
fi

echo "Rendering TLS cert"
docker run -i --rm -e LIRA_ENVIRONMENT="${LIRA_ENVIRONMENT}" \
                   -v "${VAULT_TOKEN_PATH}":/root/.vault-token:ro \
                   -v "${PWD}":/working \
                   broadinstitute/dsde-toolbox:ra_rendering \
                   /usr/local/bin/render-ctmpls.sh \
                   -k /working/"${TLS_FULL_CHAIN_DIR}".ctmpl

echo "Rendering TLS key file"
docker run -i --rm -e LIRA_ENVIRONMENT="${LIRA_ENVIRONMENT}" \
                   -v "${VAULT_TOKEN_PATH}":/root/.vault-token:ro \
                   -v "${PWD}":/working \
                   broadinstitute/dsde-toolbox:ra_rendering \
                   /usr/local/bin/render-ctmpls.sh \
                   -k /working/"${TLS_PRIVATE_KEY_DIR}".ctmpl

echo "Getting kubernetes context"
gcloud container clusters get-credentials "${KUBERNETES_CLUSTER}" \
                 --zone "${KUBERNETES_ZONE}" \
                 --project "${GCLOUD_PROJECT}"

echo "Creating TLS secret in Kubernetes"
kubectl create secret tls \
                "${TLS_SECRET_NAME}" \
                --cert="${TLS_FULL_CHAIN_DIR}" \
                --key="${TLS_PRIVATE_KEY_DIR}" \
                --namespace="${KUBERNETES_NAMESPACE}"


echo "Generating ingress file"
docker run -i --rm -e TLS_SECRET_NAME="${TLS_SECRET_NAME}" \
                   -e GLOBAL_IP_NAME="${GLOBAL_IP_NAME}" \
                   -e INGRESS_NAME="${INGRESS_NAME}" \
                   -e SERVICE_NAME="${SERVICE_NAME}" \
                   -v "${VAULT_TOKEN_PATH}":/root/.vault-token \
                   -v "${PWD}":/working \
                   broadinstitute/dsde-toolbox:ra_rendering \
                   /usr/local/bin/render-ctmpls.sh \
                   -k /working/lira-ingress.yaml.ctmpl

echo "Deploying Lira Ingress"
kubectl apply -f lira-ingress.yaml \
              --record \
              --namespace="${KUBERNETES_NAMESPACE}"

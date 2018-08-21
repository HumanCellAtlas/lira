#!/usr/bin/env bash

# Variables
LIRA_ENVIRONMENT=${LIRA_ENVIRONMENT:-"dev"} # other valid envs: test, staging, prod
GCLOUD_PROJECT=${GCLOUD_PROJECT:-"broad-dsde-mint-dev"} # other envs - broad-dsde-mint-test, broad-dsde-mint-staging, hca-dcp-pipelines-prod

GLOBAL_IP_NAME=${GLOBAL_IP_NAME:-"lira"}
KUBERNETES_NAMESPACE=${KUBERNETES_NAMESPACE:-"green-100-us-central1-ns"}
KUBERNETES_CLUSTER=${KUBERNETES_CLUSTER:-"green-100-us-central1"}
KUBERNETES_ZONE=${KUBERNETES_ZONE:-"us-central1-a"}

TLS_FULL_CHAIN_DIR=${TLS_FULL_CHAIN_DIR:-"green-wildcard-ssl-certificate.crt"}
TLS_PRIVATE_KEY_DIR=${TLS_PRIVATE_KEY_DIR:-"green-wildcard-ssl-certificate.key"}
TLS_SECRET_1_NAME=${TLS_SECRET_1_NAME:-"hca-tls-secret"-$(date '+%Y-%m-%d-%H-%M-%S')}
TLS_SECRET_2_NAME=${TLS_SECRET_2_NAME:-${TLS_SECRET_1_NAME}}
VAULT_TOKEN_PATH=${VAULT_TOKEN_PATH:-"${HOME}/.vault-token"}
INGRESS_NAME=${INGRESS_NAME:-"lira-ingress"}
SERVICE_NAME=${SERVICE_NAME:-"lira-service"}

#if [ ${LIRA_ENVIRONMENT} == "test" ];
#then
#    ENV="integration"
#else
#    ENV="${LIRA_ENVIRONMENT}"
#fi

#echo "ENV: ${ENV}"

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
                "${TLS_SECRET_1_NAME}" \
                --cert="${TLS_FULL_CHAIN_DIR}" \
                --key="${TLS_PRIVATE_KEY_DIR}" \
                --namespace="${KUBERNETES_NAMESPACE}"

if [ "${TLS_SECRET_1_NAME}" != "${TLS_SECRET_2_NAME}" ];
then
kubectl create secret tls \
                "${TLS_SECRET_2_NAME}" \
                --cert="${TLS_FULL_CHAIN_DIR}" \
                --key="${TLS_PRIVATE_KEY_DIR}" \
                --namespace="${KUBERNETES_NAMESPACE}"
fi

echo "Generating ingress file"
docker run -i --rm -e TLS_SECRET_1_NAME="${TLS_SECRET_1_NAME}" \
                   -e TLS_SECRET_2_NAME="${TLS_SECRET_2_NAME}" \
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

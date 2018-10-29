#!/usr/bin/env bash

VAULT_TOKEN_PATH=${VAULT_TOKEN_PATH:-"/etc/vault-token-dsde"}

echo "PRINTING ENVIRONMENT VARIABLES"
env

echo "PRINTING PATH"
echo "${PATH}"

echo "PRINTING PWD"
pwd

echo "Rendering deployment configuration file"
docker run -i --rm \
              -e LIRA_ENVIRONMENT="${LIRA_ENVIRONMENT}" \
              -v "${VAULT_TOKEN_PATH}":/root/.vault-token \
              -v "${PWD}":/working \
              broadinstitute/dsde-toolbox:ra_rendering \
              /usr/local/bin/render-ctmpls.sh \
              -k /working/config.sh.ctmpl

# Import the variables from the config files
source config.sh

echo "Retrieving caas service account key"
docker run -i --rm \
               -v "${VAULT_TOKEN_PATH}":/root/.vault-token \
               -v "${PWD}":/working broadinstitute/dsde-toolbox:ra_rendering \
               vault read -format=json "${CAAS_KEY_PATH}" | jq .data > "${CAAS_KEY_FILE}"

echo "Authenticating with the service account"
gcloud auth activate-service-account --key-file "${CAAS_KEY_FILE}"

echo "Rendering lira config file"
docker run -i --rm \
              -e LIRA_ENVIRONMENT="${LIRA_ENVIRONMENT}" \
              -e CROMWELL_URL="${CROMWELL_URL}" \
              -e USE_CAAS="${USE_CAAS}" \
              -e SUBMIT_AND_HOLD="${SUBMIT_AND_HOLD}" \
              -e COLLECTION_NAME="${COLLECTION_NAME}" \
              -e GCLOUD_PROJECT="${GCLOUD_PROJECT}" \
              -e GCS_ROOT="${GCS_ROOT}" \
              -e LIRA_VERSION="${LIRA_VERSION}" \
              -e DSS_URL="${DSS_URL}" \
              -e SCHEMA_URL="${SCHEMA_URL}" \
              -e INGEST_URL="${INGEST_URL}" \
              -e USE_HMAC="${USE_HMAC}" \
              -e SUBMIT_WDL="${SUBMIT_WDL}" \
              -e MAX_CROMWELL_RETRIES="${MAX_CROMWELL_RETRIES}" \
              -e TENX_ANALYSIS_WDLS="${TENX_ANALYSIS_WDLS}" \
              -e TENX_OPTIONS_LINK="${TENX_OPTIONS_LINK}" \
              -e TENX_SUBSCRIPTION_ID="${TENX_SUBSCRIPTION_ID}" \
              -e TENX_WDL_STATIC_INPUTS_LINK="${TENX_WDL_STATIC_INPUTS_LINK}" \
              -e TENX_WDL_LINK="${TENX_WDL_LINK}" \
              -e TENX_WORKFLOW_NAME="${TENX_WORKFLOW_NAME}" \
              -e TENX_VERSION="${TENX_VERSION}" \
              -e SS2_ANALYSIS_WDLS="${SS2_ANALYSIS_WDLS}" \
              -e SS2_OPTIONS_LINK="${SS2_OPTIONS_LINK}" \
              -e SS2_SUBSCRIPTION_ID="${SS2_SUBSCRIPTION_ID}" \
              -e SS2_WDL_STATIC_INPUTS_LINK="${SS2_WDL_STATIC_INPUTS_LINK}" \
              -e SS2_WDL_LINK="${SS2_WDL_LINK}" \
              -e SS2_WORKFLOW_NAME="${SS2_WORKFLOW_NAME}" \
              -e SS2_VERSION="${SS2_VERSION}" \
              -v "${VAULT_TOKEN_PATH}":/root/.vault-token \
              -v "${PWD}":/working \
              broadinstitute/dsde-toolbox:ra_rendering \
              /usr/local/bin/render-ctmpls.sh \
              -k /working/"${LIRA_CONFIG_FILE}".ctmpl

echo "Getting kubernetes context"
gcloud container clusters get-credentials "${KUBERNETES_CLUSTER}" \
                 --zone "${KUBERNETES_ZONE}" \
                 --project "${GCLOUD_PROJECT}"

echo "Deploying lira config file"
if [ ${USE_CAAS} == "true" ];
then
    kubectl create secret generic "${LIRA_CONFIG_SECRET_NAME}" \
            --from-file=config="${LIRA_CONFIG_FILE}" \
            --from-file=caas_key="${CAAS_KEY_FILE}" \
            --namespace "${KUBERNETES_NAMESPACE}"
else
    kubectl create secret generic ${LIRA_CONFIG_SECRET_NAME} \
            --from-file=config="${LIRA_CONFIG_FILE}" \
            --namespace "${KUBERNETES_NAMESPACE}"
fi

echo "Generating Lira deployment file"
docker run -i --rm -e LIRA_CONFIG="${LIRA_CONFIG_SECRET_NAME}" \
                   -e DEPLOYMENT_NAME="${DEPLOYMENT_NAME}" \
                   -e NUMBER_OF_REPLICAS="${NUMBER_OF_REPLICAS}" \
                   -e APPLICATION_NAME="${APPLICATION_NAME}" \
                   -e CONTAINER_NAME="${CONTAINER_NAME}" \
                   -e LIRA_DOCKER_IMAGE="${LIRA_DOCKER_IMAGE}" \
                   -e USE_CAAS="${USE_CAAS}" \
                   -e SUBMIT_AND_HOLD="${SUBMIT_AND_HOLD}" \
                   -v "${VAULT_TOKEN_PATH}":/root/.vault-token \
                   -v "${PWD}":/working broadinstitute/dsde-toolbox:ra_rendering \
                   /usr/local/bin/render-ctmpls.sh \
                   -k /working/"${LIRA_DEPLOYMENT_YAML}".ctmpl

echo "Deploying Lira"
kubectl apply -f lira-deployment.yaml \
              --record \
              --namespace "${KUBERNETES_NAMESPACE}"

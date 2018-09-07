#!/usr/bin/env bash

# Variables
LIRA_ENVIRONMENT=${LIRA_ENVIRONMENT:-""} # all valid envs: dev, test, integration, staging, prod
GCLOUD_PROJECT=${GCLOUD_PROJECT:-"broad-dsde-mint-dev"} # all valid envs - broad-dsde-mint-dev, broad-dsde-mint-test, broad-dsde-mint-integration, broad-dsde-mint-staging, hca-dcp-pipelines-prod

CAAS_ENVIRONMENT=${CAAS_ENVIRONMENT:-"caas-prod"}
KUBERNETES_CLUSTER=${KUBERNETES_CLUSTER:-"green-100-us-central1"}
KUBERNETES_NAMESPACE=${KUBERNETES_NAMESPACE:-"green-100-us-central1-ns"}
KUBERNETES_ZONE=${KUBERNETES_ZONE:-"us-central1-a"}
VAULT_TOKEN_PATH=${VAULT_TOKEN_PATH:-"/etc/vault-token-dsde"}

LIRA_CONFIG_FILE="lira-config.json"
LIRA_CONFIG_SECRET_NAME="lira-config-$(date '+%Y-%m-%d-%H-%M-%S')"
LIRA_DEPLOYMENT_YAML="lira-deployment.yaml"

LIRA_DOCKER_TAG=${LIRA_DOCKER_TAG:-""}
LIRA_DOCKER_IMAGE="quay.io/humancellatlas/secondary-analysis-lira:${LIRA_DOCKER_TAG}"
LIRA_VERSION=${LIRA_VERSION:-"${LIRA_DOCKER_TAG}"}

PIPELINE_TOOLS_VERSION=${PIPELINE_TOOLS_VERSION:-""}
PIPELINE_TOOLS_PREFIX="https://raw.githubusercontent.com/HumanCellAtlas/pipeline-tools/${PIPELINE_TOOLS_VERSION}"

SUBMIT_WDL_DIR=${SUBMIT_WDL_DIR:-""}

APPLICATION_NAME="lira"
MAX_CROMWELL_RETRIES=${MAX_CROMWELL_RETRIES:-"1"}

SS2_SUBSCRIPTION_ID=${SS2_SUBSCRIPTION_ID:-"placeholder_ss2_subscription_id"}
SS2_VERSION=${SS2_VERSION:-"smartseq2_v1.0.0"}
SS2_PREFIX="https://raw.githubusercontent.com/HumanCellAtlas/skylab/${SS2_VERSION}"

TENX_SUBSCRIPTION_ID=${TENX_SUBSCRIPTION_ID:-"placeholder_10x_subscription_id"}
TENX_VERSION=${TENX_VERSION:-"10x_v0.1.0"}
TENX_PREFIX="https://raw.githubusercontent.com/HumanCellAtlas/skylab/${TENX_VERSION}"

USE_CAAS=${USE_CAAS:-"true"}
USE_HMAC=${USE_HMAC:-"true"}

# Cromwell URL - usually will be caas, but can be set to local environment
CROMWELL_URL="https://cromwell.${CAAS_ENVIRONMENT}.broadinstitute.org/api/workflows/v1"

COLLECTION_NAME=${COLLECTION_NAME:-"lira-${LIRA_ENVIRONMENT}"}

# Derived Variables

# Jumping through some hoops due to mismatch of names between our environments and the environments used by the other
# teams within the HCA - this sets up the correct name for the DSS URL and the INGEST URL
if [ ${LIRA_ENVIRONMENT} == "test" ];
then
    ENV="integration"
elif [ ${LIRA_ENVIRONMENT} == "int" ];
then
    ENV="integration"
elif [ ${LIRA_ENVIRONMENT} == "dev" ];
then
    ENV="integration"
else
    ENV="${LIRA_ENVIRONMENT}"
fi

CAAS_KEY_FILE="${CAAS_ENVIRONMENT}-key.json"
CAAS_KEY_PATH="secret/dsde/mint/${LIRA_ENVIRONMENT}/${APPLICATION_NAME}/${CAAS_KEY_FILE}"

if [ ${LIRA_ENVIRONMENT} == "prod" ]
then
    DSS_URL="https://dss.data.humancellatlas.org/v1"
    SCHEMA_URL="https://schema.humancellatlas.org/"
    INGEST_URL="http://api.ingest.data.humancellatlas.org/"
else
    DSS_URL="https://dss.${ENV}.data.humancellatlas.org/v1"
    SCHEMA_URL="http://schema.${ENV}.data.humancellatlas.org/"
    INGEST_URL="http://api.ingest.${ENV}.data.humancellatlas.org/"
fi

GCS_ROOT="gs://${GCLOUD_PROJECT}-cromwell-execution/caas-cromwell-executions"

if [ -n "${SUBMIT_WDL_DIR}" ];
then
    SUBMIT_WDL="${PIPELINE_TOOLS_PREFIX}/adapter_pipelines/${SUBMIT_WDL_DIR}/submit.wdl"
else
    SUBMIT_WDL="${PIPELINE_TOOLS_PREFIX}/adapter_pipelines/submit.wdl"
fi

# Smart Seq 2 Variables
SS2_ANALYSIS_WDLS="[
                \"${SS2_PREFIX}/pipelines/smartseq2_single_sample/SmartSeq2SingleSample.wdl\",
                \"${SS2_PREFIX}/library/tasks/HISAT2.wdl\",
                \"${SS2_PREFIX}/library/tasks/Picard.wdl\",
                \"${SS2_PREFIX}/library/tasks/RSEM.wdl\"
            ]"
SS2_OPTIONS_LINK="${PIPELINE_TOOLS_PREFIX}/adapter_pipelines/ss2_single_sample/options.json"
SS2_WDL_STATIC_INPUTS_LINK="${PIPELINE_TOOLS_PREFIX}/adapter_pipelines/ss2_single_sample/adapter_example_static.json"
SS2_WDL_LINK="${PIPELINE_TOOLS_PREFIX}/adapter_pipelines/ss2_single_sample/adapter.wdl"
SS2_WORKFLOW_NAME="AdapterSmartSeq2SingleCell"

# TenX Variables
TENX_ANALYSIS_WDLS="[
                \"${TENX_PREFIX}/pipelines/10x/count/count.wdl\"
            ]"
TENX_OPTIONS_LINK="${PIPELINE_TOOLS_PREFIX}/adapter_pipelines/10x/options.json"
TENX_WDL_STATIC_INPUTS_LINK="${PIPELINE_TOOLS_PREFIX}/adapter_pipelines/10x/adapter_example_static.json"
TENX_WDL_LINK="${PIPELINE_TOOLS_PREFIX}/adapter_pipelines/10x/adapter.wdl"
TENX_WORKFLOW_NAME="Adapter10xCount"

DEPLOYMENT_NAME=${DEPLOYMENT_NAME:-"lira"}
NUMBER_OF_REPLICAS=${NUMBER_OF_REPLICAS:-"3"}
CONTAINER_NAME=${CONTAINER_NAME:-"lira"}

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
                   -v "${VAULT_TOKEN_PATH}":/root/.vault-token \
                   -v "${PWD}":/working broadinstitute/dsde-toolbox:ra_rendering \
                   /usr/local/bin/render-ctmpls.sh \
                   -k /working/"${LIRA_DEPLOYMENT_YAML}".ctmpl

echo "Deploying Lira"
kubectl apply -f lira-deployment.yaml \
              --record \
              --namespace "${KUBERNETES_NAMESPACE}"

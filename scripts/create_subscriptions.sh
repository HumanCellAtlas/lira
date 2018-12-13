#!/usr/bin/env bash

# Please Note: the dss storage service white list may need to be updated
# (https://github.com/HumanCellAtlas/data-store/blob/master/environment#L63) to include the
# bluebox-subscription-manager@<GCLOUD_PROJECT>.iam.gserviceaccount.com service account

# Variables
LIRA_ENVIRONMENT=${LIRA_ENVIRONMENT:-""}
GCLOUD_PROJECT=${GCLOUD_PROJECT:-"broad-dsde-mint-${LIRA_ENVIRONMENT}"}
if [ ${LIRA_ENVIRONMENT} == "prod" ];
then
    GCLOUD_PROJECT="hca-dcp-pipelines-prod"
fi

SERVICE="lira"
VAULT_TOKEN_PATH=${VAULT_TOKEN_PATH:-"${HOME}/.vault-token"}

# Derived variables
if [ ${LIRA_ENVIRONMENT} == "test" ];
then
    ENV="integration"
elif [ ${LIRA_ENVIRONMENT} == "dev" ];
then
    ENV="integration"
else
    ENV="${LIRA_ENVIRONMENT}"
fi

if [ ${LIRA_ENVIRONMENT} == "prod" ]
then
    DSS_URL="https://dss.data.humancellatlas.org/v1"
    LIRA_URL="https://pipelines.data.humancellatlas.org/notifications"
else
    DSS_URL="https://dss.${ENV}.data.humancellatlas.org/v1"
    LIRA_URL="https://pipelines.${ENV}.data.humancellatlas.org/notifications"
fi

BLUEBOX_SUBSCRIPTION_KEY="bluebox-subscription-manager-${LIRA_ENVIRONMENT}-key.json"
BLUEBOX_SUBSCRIPTION_PATH="secret/dsde/mint/${LIRA_ENVIRONMENT}/${SERVICE}/${BLUEBOX_SUBSCRIPTION_KEY}"
BLUEBOX_IAM_ACCOUNT="bluebox-subscription-manager@${GCLOUD_PROJECT}.iam.gserviceaccount.com"

HMAC_KEY_FILE="hmac_keys"
HMAC_KEY_PATH="secret/dsde/mint/${LIRA_ENVIRONMENT}/${SERVICE}/${HMAC_KEY_FILE}"

gcloud config set project ${GCLOUD_PROJECT}

# Create bluebox service account & key
echo "Creating bluebox-subscription-manager service account and key"
gcloud iam service-accounts create bluebox-subscription-manager \
                            --display-name=bluebox-subscription-manager

gcloud iam service-accounts keys create ${BLUEBOX_SUBSCRIPTION_KEY} \
                            --iam-account=${BLUEBOX_IAM_ACCOUNT}

# Add service account key to vault
docker run -it --rm \
               -v ${VAULT_TOKEN_PATH}:/root/.vault-token \
               -v ${PWD}:/working \
               broadinstitute/dsde-toolbox:ra_rendering \
               vault write "${BLUEBOX_SUBSCRIPTION_PATH}" \
               @/working/"${BLUEBOX_SUBSCRIPTION_KEY}"

# Get the lira secret from vault
# Note: This value is not used in this script for now. This script only supports making subscriptions with HMAC method
LIRA_SECRET=$(docker run -it --rm -v ${VAULT_TOKEN_PATH}:/root/.vault-token broadinstitute/dsde-toolbox:ra_rendering vault read -field=notification_token secret/dsde/mint/${ENV}/lira/lira_secret)

BLUEBOX_KEY_PATH=${PWD}/${BLUEBOX_SUBSCRIPTION_KEY}

docker run -i --rm \
               -v "${VAULT_TOKEN_PATH}":/root/.vault-token \
               -v "${PWD}":/working broadinstitute/dsde-toolbox:ra_rendering \
               vault read -format=json "${HMAC_KEY_PATH}" > "${HMAC_KEY_FILE}"

ADDITIONAL_METADATA=${ADDITIONAL_METADATA:-"v6_queries/metadata_attachments.json"}
SMART_SEQ_2_QUERY=${SMART_SEQ_2_QUERY:-"v6_queries/smartseq2-query.json"}
TENX_QUERY=${TENX_QUERY:-"v6_queries/10x-query.json"}

#echo "Creating ss2 subscription"
SS2_SUBSCRIPTION_ID=$(python3 subscribe.py create --dss_url="${DSS_URL}" \
                            --key_file="${BLUEBOX_KEY_PATH}" \
                            --google_project="${GCLOUD_PROJECT}" \
                            --replica="gcp" \
                            --callback_base_url="${LIRA_URL}" \
                            --query_json="${SMART_SEQ_2_QUERY}" \
                            --hmac_key_id="$(cat ${HMAC_KEY_FILE} | jq .data | jq 'keys[]')" \
                            --hmac_key="$(cat ${HMAC_KEY_FILE} | jq .data | jq 'values[]')" \
                            --additional_metadata="${ADDITIONAL_METADATA}")

echo "${SS2_SUBSCRIPTION_ID}"

#echo "Creating 10x subscription"
TENX_SUBSCRIPTION_ID=$(python3 subscribe.py create --dss_url="${DSS_URL}" \
                            --key_file="${BLUEBOX_KEY_PATH}" \
                            --google_project="${GCLOUD_PROJECT}" \
                            --replica="gcp" \
                            --callback_base_url="${LIRA_URL}" \
                            --query_json="${TENX_QUERY}" \
                            --hmac_key_id="$(cat ${HMAC_KEY_FILE} | jq .data | jq 'keys[]')" \
                            --hmac_key="$(cat ${HMAC_KEY_FILE} | jq .data | jq 'values[]')" \
                            --additional_metadata="${ADDITIONAL_METADATA}")

echo "${TENX_SUBSCRIPTION_ID}"

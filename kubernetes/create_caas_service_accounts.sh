#!/usr/bin/env bash
# This script creates service accounts in the specified gcloud project
# It then registers it in both FireCloud and SAM for use with Cromwell-as-a-Service (CaaS).


# Variables
LIRA_ENVIRONMENT=${LIRA_ENVIRONMENT:-""}
GCLOUD_PROJECT=${GCLOUD_PROJECT:-"broad-dsde-mint-${LIRA_ENVIRONMENT}"}
if [ ${LIRA_ENVIRONMENT} == "prod" ];
then
    GCLOUD_PROJECT="hca-dcp-pipelines-prod"
fi

CAAS_ENVIRONMENT=${CAAS_ENVIRONMENT:-"caas-prod"}
SAM_ENVIRONMENT=${SAM_ENVIRONMENT:-"prod"}
FIRECLOUD_ENVIRONMENT=${FIRECLOUD_ENVIRONMENT:-"prod"}

VAULT_TOKEN_PATH=${VAULT_TOKEN_PATH:-"${HOME}/.vault-token"}

FIRECLOUD_USER_GROUP_NAME=${FIRECLOUD_USER_GROUP_NAME:-"mint-${LIRA_ENVIRONMENT}-write-access"}
FIRECLOUD_API_URL=${FIRECLOUD_API_URL:-"https://firecloud-orchestration.dsde-${FIRECLOUD_ENVIRONMENT}.broadinstitute.org"}

if [ "${FIRECLOUD_ENVIRONMENT}" == "prod" ];
then
    FIRECLOUD_API_URL="https://api.firecloud.org"
fi

if [ "${LIRA_ENVIRONMENT}" == "integration" ];
then
    ENV="int"
elif [ "${LIRA_ENVIRONMENT}" == "prod" ];
then
    ENV="hca-prod"
else
    ENV="${LIRA_ENVIRONMENT}"
fi

SAM_URL=${SAM_URL:-"https://sam.dsde-${SAM_ENVIRONMENT}.broadinstitute.org"}

# Derived variables
WORKFLOW_COLLECTION_ID="lira-${LIRA_ENVIRONMENT}"
SVC_ACCOUNT_NAME="${CAAS_ENVIRONMENT}-account-for-${ENV}"
SVC_ACCOUNT_EMAIL="${SVC_ACCOUNT_NAME}@${GCLOUD_PROJECT}.iam.gserviceaccount.com"
SVC_ACCOUNT_KEY="${CAAS_ENVIRONMENT}-key.json"
SVC_ACCOUNT_VAULT_KEY_PATH="secret/dsde/mint/${LIRA_ENVIRONMENT}/lira/${SVC_ACCOUNT_KEY}"

#Set gcloud project
gcloud config set project ${GCLOUD_PROJECT}

# Create the service account
gcloud iam service-accounts create ${SVC_ACCOUNT_NAME} \
           --display-name=${SVC_ACCOUNT_NAME}

# Grant the service account the necessary permissions
gcloud beta projects add-iam-policy-binding \
            ${GCLOUD_PROJECT} \
            --member="serviceAccount:${SVC_ACCOUNT_EMAIL}" \
            --role 'roles/compute.instanceAdmin'

gcloud beta projects add-iam-policy-binding \
            ${GCLOUD_PROJECT} \
            --member="serviceAccount:${SVC_ACCOUNT_EMAIL}" \
            --role 'roles/genomics.pipelinesRunner'

gcloud beta projects add-iam-policy-binding \
            ${GCLOUD_PROJECT} \
            --member="serviceAccount:${SVC_ACCOUNT_EMAIL}" \
            --role 'roles/serviceusage.serviceUsageConsumer'

gcloud beta projects add-iam-policy-binding \
            ${GCLOUD_PROJECT} \
            --member="serviceAccount:${SVC_ACCOUNT_EMAIL}" \
            --role 'roles/storage.objectAdmin'

gcloud beta projects add-iam-policy-binding \
            ${GCLOUD_PROJECT} \
            --member="serviceAccount:${SVC_ACCOUNT_EMAIL}" \
            --role 'roles/container.admin'

# create keys for the service account
gcloud iam service-accounts keys create "${SVC_ACCOUNT_KEY}" \
            --iam-account="${SVC_ACCOUNT_EMAIL}" \
            --key-file-type=json

# Add the service account key to vault
docker run -it --rm -v "${VAULT_TOKEN_PATH}":/root/.vault-token \
                    -v "${PWD}":/keys broadinstitute/dsde-toolbox:ra_rendering \
                    vault write "${SVC_ACCOUNT_VAULT_KEY_PATH}" \
                    @"/keys/${SVC_ACCOUNT_KEY}"

echo "Registering the service account for use in Firecloud"
python3 register_service_account.py -j "${SVC_ACCOUNT_KEY}" \
                                   -e "${SVC_ACCOUNT_EMAIL}" \
                                   -u "${FIRECLOUD_API_URL}"

echo "Registering the service account in SAM"
python3 sam_registration.py \
    --json_credentials "${SVC_ACCOUNT_KEY}" \
    --workflow_collection_id "${WORKFLOW_COLLECTION_ID}" \
    --firecloud_group_name "${FIRECLOUD_USER_GROUP_NAME}" \
    --sam_url "${SAM_URL}" \
    --firecloud_api_url "${FIRECLOUD_API_URL}"

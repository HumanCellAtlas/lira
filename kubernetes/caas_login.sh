#!/usr/bin/env bash
# This script creates a service account in the specified gcloud project and registers it in FireCloud and SAM for use with Cromwell-as-a-service (CaaS).
# Note: CaaS is only available in dev, so this script uses the develop versions of FireCloud and SAM

GCLOUD_PROJECT=$1  # The gcloud project in which to create the service account
ENV=$2  # The deployment environment associated with the gcloud project
KEY_DIR=$3  # Where to save the service account key
WORKFLOW_COLLECTION_ID=$4  # The name of the workflow-collection to create in SAM (e.g. "dev-workflows")
FIRECLOUD_CONTACT_EMAIL=$5  # A contact email to use for the FireCloud service account
FIRECLOUD_GROUP_NAME=$6  # The name of the user group to create in FireCloud to control workflow collection permissions (e.g. "write-access")
VAULT_TOKEN_FILE=${VAULT_TOKEN_FILE:-"$HOME/.vault-token"}
FIRECLOUD_URL=${FIRECLOUD_URL:-"https://firecloud.dsde-dev.broadinstitute.org"}
FIRECLOUD_API_URL=${FIRECLOUD_URL:-"https://firecloud-orchestration.dsde-dev.broadinstitute.org"}
SAM_URL=${SAM_URL:-"https://sam.dsde-dev.broadinstitute.org"}


#Set gcloud project
gcloud config set project ${GCLOUD_PROJECT}

echo "Creating CaaS service account and key"
KEY_FILE_PATH=${KEY_DIR}/caas-${ENV}-key.json
IAM_ACCOUNT_EMAIL=caas-account@${GCLOUD_PROJECT}.iam.gserviceaccount.com
gcloud iam service-accounts create caas-account --display-name=caas-account
gcloud iam service-accounts keys create ${KEY_FILE_PATH} --iam-account=${IAM_ACCOUNT_EMAIL}

# Add key to vault
docker run -it --rm -v ${VAULT_TOKEN_FILE}:/root/.vault-token -v ${KEY_DIR}:/keys broadinstitute/dsde-toolbox vault write secret/dsde/mint/${ENV}/listener/caas-${ENV}-key.json @/keys/caas-${ENV}-key.json

# Clone firecloud-tools repo
git clone git@github.com:broadinstitute/firecloud-tools.git
cd firecloud-tools

echo "Register the service account for use in Firecloud"
./run.sh scripts/register_service_account/register_service_account.py -j ${KEY_FILE_PATH} -e ${FIRECLOUD_CONTACT_EMAIL} -u ${FIRECLOUD_URL}

cd ..

echo "Register the service account in SAM"
./sam_registration.py \
    --json_credentials ${KEY_FILE_PATH} \
    --workflow_collection_id ${WORKFLOW_COLLECTION_ID} \
    --firecloud_group_name ${FIRECLOUD_GROUP_NAME} \
    --sam_url ${SAM_URL} \
    --firecloud_api_url ${FIRECLOUD_API_URL}

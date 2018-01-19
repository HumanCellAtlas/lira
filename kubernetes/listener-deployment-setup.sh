#!/usr/bin/env bash

# Create subscriptions to the HCA Data Storage Service for the 10x and ss2 pipelines and generate a config.json file
# for a new lira deployment that will run the 10x and ss2 pipelines. Prior to running this script:
#   - Update the dss storage service white list (https://github.com/HumanCellAtlas/data-store/blob/master/environment#L63)
#     to include bluebox-subscription-manager@<GCLOUD_PROJECT>.iam.gserviceaccount.com


ENV=$1  #name of the deployment environment (e.g. staging)
GCLOUD_PROJECT=$2  #ID of the gcloud project (e.g. broad-dsde-mint-staging)
BLUEBOX_SUBSCRIPTION_KEY_DIR=$3  #absolute path of the subscription key
DSS_URL=$4
PIPELINE_TOOLS_PREFIX=$5
SS2_PREFIX=$6
TENX_PREFIX=$7
VAULT_TOKEN_FILE=${VAULT_TOKEN_FILE:-"$HOME/.vault-token"}

if [ -z $ENV ]; then
    echo -e "\nYou must specify a deployment environment"
    error=1
elif [ -z $GCLOUD_PROJECT ]; then
    echo -e "\nYou must specify a gcloud project for the deployment"
    error=1
elif [ -z $BLUEBOX_SUBSCRIPTION_KEY_DIR ]; then
    echo -e "\nYou must specify a directory in which to store the bluebox subscription key file"
    error=1
elif [ -z $DSS_URL ]; then
    echo -e "\nYou must specify a dss url"
    error=1
elif [ -z $PIPELINE_TOOLS_PREFIX ]; then
    echo -e "\nYou must specify the pipeline-tools prefix"
    error=1
elif [ -z $SS2_PREFIX ]; then
    echo -e "\nYou must specify the SmartSeq2 prefix"
    error=1
elif [ -z $TENX_PREFIX ]; then
    echo -e "\nYou must specify the 10x prefix"
    error=1
fi

if [ $error -eq 1 ]; then
    echo -e "\nUsage: bash listener-deployment.sh ENV GCLOUD_PROJECT BLUBOX_SUBSCRIPTION_KEY_DIR DSS_URL PIPELINE_TOOLS_PREFIX SS2_PREFIX TENX_PREFIX\n"
    exit 1
fi


# Set gcloud project
gcloud config set project ${GCLOUD_PROJECT}

# Create service account & key
echo "Creating bluebox-subscription-manager service account and key"
KEY_FILE_PATH=${BLUEBOX_SUBSCRIPTION_KEY_DIR}/bluebox-subscription-manager-${ENV}-key.json
gcloud iam service-accounts create bluebox-subscription-manager --display-name=bluebox-subscription-manager
gcloud iam service-accounts keys create ${KEY_FILE_PATH} --iam-account=bluebox-subscription-manager@${GCLOUD_PROJECT}.iam.gserviceaccount.com

# Add key to vault
docker run -it --rm -v ${VAULT_TOKEN_FILE}:/root/.vault-token -v ${BLUEBOX_SUBSCRIPTION_KEY_DIR}:/keys broadinstitute/dsde-toolbox vault write secret/dsde/mint/${ENV}/listener/bluebox-subscription-manager-${ENV}-key.json @/keys/bluebox-subscription-manager-${ENV}-key.json

# Create subscriptions for ss2 and 10x queries
GREEN_URL=https://pipelines.${ENV}.data.humancellatlas.org/notifications
LISTENER_SECRET=$(docker run -it --rm -v ${VAULT_TOKEN_FILE}:/root/.vault-token broadinstitute/dsde-toolbox vault read -field=notification_token secret/dsde/mint/${ENV}/listener/listener_secret)

cd ../scripts

echo "Creating ss2 subscription"
SS2_SUBSCRIPTION_ID=$(bash subscription-create.sh ${DSS_URL} ${GREEN_URL} ${KEY_FILE_PATH} ${LISTENER_SECRET} v4_queries/smartseq2-query.json | jq '.[]')
echo ${SS2_SUBSCRIPTION_ID}

echo "Creating 10x subscription"
TENX_SUBSCRIPTION_ID=$(bash subscription-create.sh ${DSS_URL} ${GREEN_URL} ${KEY_FILE_PATH} ${LISTENER_SECRET} v4_queries/10x-query.json | jq '.[]')
echo ${TENX_SUBSCRIPTION_ID}

cd ../kubernetes

# Generate config
echo "Creating Lira config"
docker run -i --rm \
    -e INPUT_PATH=/working \
    -e OUT_PATH=/working \
    -e ENV=${ENV} \
    -e NOTIFICATION_TOKEN=${LISTENER_SECRET} \
    -e PIPELINE_TOOLS_PREFIX=${PIPELINE_TOOLS_PREFIX} \
    -e SS2_PREFIX=${SS2_PREFIX} \
    -e SS2_SUBSCRIPTION_ID=${SS2_SUBSCRIPTION_ID} \
    -e TENX_PREFIX=${TENX_PREFIX} \
    -e TENX_SUBSCRIPTION_ID=${TENX_SUBSCRIPTION_ID} \
    -v ${VAULT_TOKEN_FILE}:/root/.vault-token \
    -v ${PWD}:/working broadinstitute/dsde-toolbox:k8s \
    /usr/local/bin/render-ctmpl.sh -k /working/listener-config.json.ctmpl

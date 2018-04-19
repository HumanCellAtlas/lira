#!/usr/bin/env bash

# Create a new lira deployment with Kubernetes on Google Compute Engine. Prior to running the script:
#   - Generate a config.json file with listener-deployment-setup.sh
#   - Generate TLS certificates and put them in the same directory as config.json

ENV=$1
VAULT_TOKEN=$2
CERT_DIR=$3
FULLCHAIN_FILENAME=$4
PRIVKEY_FILENAME=$5
DNS_ZONE_NAME=$6
DOCKER_TAG=$7 # version of the quay.io/humancellatlas/secondary-analysis-lira image to deploy
GCLOUD_PROJECT=$8
USE_CAAS=$9  # whether or not to use cromwell-as-a-service
WORKFLOW_COLLECTION_ID=${10}  # The name of the workflow-collection to create in SAM (e.g. "dev-workflows")
FIRECLOUD_CONTACT_EMAIL=${11}  # A contact email to use for the FireCloud service account
FIRECLOUD_GROUP_NAME=${12}  # The name of the user group to create in FireCloud to control workflow collection permissions (e.g. "write-access")

GET_CERTS=${GET_CERTS:-"false"}
VAULT_TOKEN_FILE=${VAULT_TOKEN_FILE:-"$HOME/.vault-token"}
KUBE_YAML=${KUBE_YAML:-"listener-deployment.yaml"}

DOMAIN=${DOMAIN:-"broadinstitute.org"}
PUBLIC_DOMAIN=${PUBLIC_DOMAIN:-"data.humancellatlas.org"}
PUBLIC_URL=${PUBLIC_URL:-"pipelines.$ENV.$PUBLIC_DOMAIN"}

if [ -z $ENV ]; then
    echo -e "\nYou must specify a deployment environment"
    error=1
elif [ -z $VAULT_TOKEN ]; then
    echo -e "\nYou must specify a github vault token"
    error=1
elif [ -z $CERT_DIR ]; then
    echo -e "\nYou must specify a path to the directory containing the certificates and listener config"
    error=1
elif [ -z $FULLCHAIN_FILENAME ]; then
    echo -e "\nYou must specify the name of the fullchain pem file to use"
    error=1
elif [ -z $PRIVKEY_FILENAME ]; then
    echo -e "\nYou must specify the name of the privkey pem file to use"
    error=1
elif [ -z $DNS_ZONE_NAME ]; then
    echo -e "\nYou must specify the name of the gcloud DNS zone to create"
    error=1
elif [ -z $DOCKER_TAG ]; then
    echo -e "\nYou must specify the lira docker version to deploy"
    error=1
elif [ -z $GCLOUD_PROJECT ]; then
    echo -e "\nYou must specify a gcloud project for the deployment"
    error=1
elif [ -z $USE_CAAS ]; then
    echo -e "\nYou must specify whether to use Cromwell-as-a-Service"
    error=1
fi

if [ $error -eq 1 ]; then
    echo -e "\nUsage: bash listener-deployment.sh ENV VAULT_TOKEN CERT_DIR FULLCHAIN_FILENAME PRIVKEY_FILENAME DNS_ZONE_NAME DOCKER_TAG\n"
    exit 1
fi


#Set gcloud project
gcloud config set project ${GCLOUD_PROJECT}

# Create listener cluster
printf "\ncreate listener cluster"
gcloud container clusters create listener

printf "\nauthenticate to vault"
docker run -it --rm \
    -v $HOME:/root:rw \
    broadinstitute/dsde-toolbox vault auth -method=github token=$VAULT_TOKEN

# If no path to certificates are provided, get them from vault:
if [ $GET_CERTS == "true" ]; then
    printf "\nget certificates from vault"

    docker run -it --rm -v ${VAULT_TOKEN_FILE}:/root/.vault-token broadinstitute/dsde-toolbox vault read -format=json -field=value secret/dsde/mint/${ENV}/listener/$FULLCHAIN_FILENAME > $CERT_DIR/fullchain.pem

    docker run -it --rm -v ${VAULT_TOKEN_FILE}:/root/.vault-token broadinstitute/dsde-toolbox vault read -format=json -field=value secret/dsde/mint/${ENV}/listener/$PRIVKEY_FILENAME > $CERT_DIR/privkey.pem
fi

# Set tls secret:
printf "\nsetting tls secret"
TLS_SECRET_NAME=$(bash populate-tls-secret.sh "hca-tls-secret" ${CERT_DIR})

# Create static ip address
printf "\ncreating static IP address"
gcloud compute addresses create listener --global

# Create DNS zone
ZONE=${DNS_ZONE_NAME}
DNS_NAME=${ZONE}.${DOMAIN}.
gcloud dns managed-zones create ${ZONE} --dns-name ${DNS_NAME} --description "${DNS_NAME} zone"

# Add a record-set that points to the static ip address
IP_ADDRESS=$(gcloud compute addresses describe listener --global --format='value(address)')
echo ${IP_ADDRESS}
RECORD_NAME=listener101.${ZONE}.${DOMAIN}

gcloud dns record-sets transaction start -z=${ZONE}
gcloud dns record-sets transaction add ${IP_ADDRESS} --zone ${ZONE} --name ${RECORD_NAME} --ttl 300 --type A
gcloud dns record-sets transaction execute -z=${ZONE}

# Add a CNAME record set to AWS
printf -v QUERY 'HostedZones[?Name == `%s`].Id' "${PUBLIC_DOMAIN}."

# Parse the query result "/hostedzone/ABCDE" to get only the hosted zone id ABCDE
HOSTED_ZONE_ID="$(aws route53 list-hosted-zones --query "${QUERY}" --output text | cut -d "/" -f 3)"

printf "Add AWS CNAME record"
aws route53 change-resource-record-sets \
    --hosted-zone-id "${HOSTED_ZONE_ID}" \
    --change-batch "{
      \"Changes\": [{
        \"Action\": \"CREATE\",
        \"ResourceRecordSet\": {
          \"Name\": \"${PUBLIC_URL}.\",
          \"ResourceRecords\": [{\"Value\": \"${RECORD_NAME}\"}],
          \"Type\": \"CNAME\",
          \"TTL\": 60
        }
      }]
    }"


# Set listener config secret
printf "\nset listener config secret"
CONFIG_FILE=$CERT_DIR/config.json

if $USE_CAAS; then
    bash caas_login.sh ${GCLOUD_PROJECT} ${ENV} ${CERT_DIR} ${WORKFLOW_COLLECTION_ID} ${FIRECLOUD_CONTACT_EMAIL} ${FIRECLOUD_GROUP_NAME}
    CAAS_KEY_FILE=$CERT_DIR/caas-${ENV}-key.json
    CONFIG_SECRET_NAME=$(bash populate-listener-config-secret.sh $CONFIG_FILE $CAAS_KEY_FILE)
else
    CONFIG_SECRET_NAME=$(bash populate-listener-config-secret.sh $CONFIG_FILE)
fi

# Generate listener-deployment.yaml image with the docker image to deploy
docker run -i --rm -e LIRA_CONFIG=${CONFIG_SECRET_NAME} -e DOCKER_TAG=${DOCKER_TAG} -e USE_CAAS=${USE_CAAS} -v ${VAULT_TOKEN_FILE}:/root/.vault-token -v ${PWD}:/working broadinstitute/dsde-toolbox:k8s /usr/local/bin/render-ctmpl.sh -k /working/${KUBE_YAML}.ctmpl

# Create deployment
printf "\ncreating listener deployment"
kubectl create -f listener-deployment.yaml --record --save-config

# Create service
printf "\ncreating listener service"
kubectl create -f listener-service.yaml --record --save-config

# Generate listener-ingress.yaml file using the tls secret
docker run -i --rm -e TLS_SECRET_NAME=${TLS_SECRET_NAME} -v ${VAULT_TOKEN_FILE}:/root/.vault-token -v ${PWD}:/working broadinstitute/dsde-toolbox:k8s /usr/local/bin/render-ctmpl.sh -k /working/listener-ingress.yaml.ctmpl

# Create ingress
printf "\ncreating listener ingress"
kubectl create -f listener-ingress.yaml --record --save-config

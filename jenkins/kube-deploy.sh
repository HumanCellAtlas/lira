#!/bin/bash

set -ex

#  This script is designed to be run by jenkins to deploy a new kubernetes
#  deployment.

# Environment vars expected to be set
#
#  ENV: environment to deploy for.  Used in ctmpls to set certain values
#  GOOGLE_PROJECT: google project to deploy into
#    (if not set derive from ENV)
#  KUBE_CLUSTER: kubernetes cluster name to deploy to
#    (if not set see if there is only one kube cluster in project then use that)

# vault path for service account
KUBE_SVC_ACCT_PATH="secret/dsde/dsp-techops/common/kube-admin-service-account.json"
KUBE_SVC_ACCT_JSON="kube-admin-service-account.json"

# vault token file
VAULT_TOKEN_FILE=${VAULT_TOKEN_FILE:-"/etc/vault-token-dsde"}

# google project
GOOGLE_PROJECT=${GOOGLE_PROJECT:-"broad-dsde-mint-${ENV}"}

# kubernetes yaml to deploy
KUBE_YAML="lira-deployment.yaml"

# namespace
KUBE_NAMESPACE=${KUBE_NAMESPACE:-"default"}

KUBE_CLUSTER=${KUBE_CLUSTER:-"lira"}

# set up temp dir to isolate gcloud commands
build_tmp="${WORKSPACE}/${BUILD_TAG}"
mkdir ${build_tmp}

export CLOUDSDK_CONFIG="${build_tmp}"

errorout() {
  echo "Error occurred - exiting"
  exit 1
}

# verify required environment vars are set
# if [ -z "${KUBE_CLUSTER}" ]
# then
#   errorout
# fi

# add validation of vault token
# vault token-lookup

# get DSP service acct json from vault
docker run -i --rm -v ${VAULT_TOKEN_FILE}:/root/.vault-token  broadinstitute/dsde-toolbox vault read --format=json ${KUBE_SVC_ACCT_PATH} | jq .data > ${KUBE_SVC_ACCT_JSON}
# check return
 
# gcloud auth activate DSP service acct
gcloud auth activate-service-account --key-file=${KUBE_SVC_ACCT_JSON}
# check return
 
# verify access to google project

# gcloud container clusters list - find kube cluster name
clusters=$(gcloud --format=json container --project ${GOOGLE_PROJECT} clusters list | jq .[].name | tr -d '"')
# check return

num_clusters=$(echo $clusters| wc -w ) 

if [[ -z "${KUBE_CLUSTER}" ]] && [[ $num_clusters -ne 1 ]]
then
  errorout "Unable to determine cluster to deploy to"
fi
 
if [ $num_clusters -eq 0 ]
then
  errorout "No cluster to deploy to"
fi

#
KUBE_CLUSTER=${KUBE_CLUSTER:-"${clusters}"}

# get zone of cluster
cluster_zone=$(gcloud --format=json container --project ${GOOGLE_PROJECT} clusters list --filter name=${KUBE_CLUSTER} | jq .[].zone | tr -d '"')
# check return

# gcloud container --projects PROJ clusters --zone get-credentials <CLUSTNAME>
gcloud container --project ${GOOGLE_PROJECT} clusters --zone ${cluster_zone} get-credentials ${KUBE_CLUSTER}
# check return

# context should already be set 
context="gke_${GOOGLE_PROJECT}_${ZONE}_${KUBE_CLUSTER}"

# run get to compare to above and set if not set correctly
# kubectl config get-contexts
# kubectl config use-context <CONTEXT_NAME>
# CONTEXT_NAME=gke_<GOOGLE_PROJ>_<ZONE>_<CLUSTER_NAME>

# Now you should be able to run kubectl commands

# render any configs
# should we render all ctmpls or just the one deployed

# should check if yaml needs rendering

# Render template for deployment
docker run -i \
           --rm  ${DOCKER_OPTS} \
           -e LIRA_CONFIG=${LIRA_CONFIG} \
           -e DOCKER_TAG=${DOCKER_TAG} \
           -e ENV=${ENV} \
           -e USE_CAAS=${USE_CAAS} \
           -v ${VAULT_TOKEN_FILE}:/root/.vault-token \
           -v ${PWD}/kubernetes:/working broadinstitute/dsde-toolbox:ra_rendering \
           /usr/local/bin/render-ctmpls.sh \
           /working/${KUBE_YAML}.ctmpl

# kube  commands

# kubectl get pods to see if already running

# if running command is apply  else command is create
command="apply"

kubectl ${command} --namespace=${KUBE_NAMESPACE} -f kubernetes/${KUBE_YAML}
# check return

# since deployment may take time should loop waiting for kubernetes to complete
# deployment

# 
exit 0

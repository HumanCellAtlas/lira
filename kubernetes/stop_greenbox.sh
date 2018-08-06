#!/usr/bin/env bash

# WARNING: This script stops all greenbox services and workflows.
# Example usage: bash stop_greenbox.sh gke_dev_context https://example-cromwell.org/api/workflows/v1 dev

KUBE_CONTEXT=$1
CROMWELL_URL=$2
VAULT_ENV=$3
DRY_RUN=$4
VAULT_TOKEN_FILE=${VAULT_TOKEN_FILE:-"$HOME/.vault-token"}

if [ -z $KUBE_CONTEXT ]; then
    echo -e "\nYou must specify a Kubernetes context to use"
    error=1
elif [ -z $CROMWELL_URL ]; then
    echo -e "\nYou must specify a Cromwell url"
    error=1
elif [ -z $VAULT_ENV ]; then
    echo -e "\nYou must specify a vault environment for getting the CaaS service account key"
    error=1
elif [ -z $DRY_RUN ]; then
    DRY_RUN = "false"
fi
if [ $error -eq 1 ]; then
    echo -e "\nUsage: bash stop_greenbox.sh KUBE_CONTEXT CROMWELL_URL VAULT_ENV\n"
    exit 1
fi

kubectl config use-context ${KUBE_CONTEXT}

# Delete ingress rule for Lira to stop receiving notifications
echo "Delete Lira ingress"
if [ $DRY_RUN == "false" ]; then
    kubectl delete ingress listener
fi

# Bring down Falcon to stop releasing workflows
# TODO: Uncomment when Falcon is deployed
# echo "Delete Falcon deployment"
# if [ $DRY_RUN == 'false' ]; then
# kubectl delete deployment falcon
# fi

CAAS_KEY_FILE="caas_key.json"
docker run -i --rm -e VAULT_TOKEN=$(cat $VAULT_TOKEN_FILE) broadinstitute/dsde-toolbox vault read \
        -format=json \
        -field=value \
        secret/dsde/mint/$VAULT_ENV/listener/caas-${VAULT_ENV}-key.json > $CAAS_KEY_FILE

# Abort all on-hold and running workflows
python -m abort_workflows --cromwell_url ${CROMWELL_URL} --caas_key ${CAAS_KEY_FILE} --dry_run ${DRY_RUN}

#!/usr/bin/env bash

export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/local/google-cloud-sdk/bin

export VAULT_TOKEN_PATH="/gitlab-runner/.vault-token"
export VAULT_TOKEN="$(cat ${VAULT_TOKEN_PATH})"

export WORK_DIR=$(pwd)
export CONFIG_DIR=${WORK_DIR}/deploy/config_files
export DEPLOY_DIR=${WORK_DIR}/deploy/gitlab

echo "Rendering deployment configuration file"
sh /usr/local/bin/render-ctmpls.sh -k ${CONFIG_DIR}/config.sh.ctmpl

# Import the variables from the config files
source ${CONFIG_DIR}/config.sh

echo "Retrieving caas service account key"
vault read -format=json "${CAAS_KEY_PATH}" | jq .data > "${CONFIG_DIR}/${CAAS_KEY_FILE}"

echo "Authenticating with the service account"
gcloud auth activate-service-account --key-file "${CONFIG_DIR}/${CAAS_KEY_FILE}"

echo "Getting kubernetes context"
gcloud container clusters get-credentials "${KUBERNETES_CLUSTER}" \
                 --zone "${KUBERNETES_ZONE}" \
                 --project "${GCLOUD_PROJECT}"




# Generate and apply the the lira service file
echo "Generating service file"
sh /usr/local/bin/render-ctmpls.sh -k lira-service.yaml.ctmpl

echo "Deploying Lira Service"
kubectl apply -f ${CONFIG_DIR}/lira-service.yaml \
              --record \
              --namespace="${KUBERNETES_NAMESPACE}"




# Generate and apply the tls cert and ingress files
if [ ${GENERATE_CERTS} == "true" ];
then
    ../../kubernetes/get_certs.sh
fi

echo "Rendering TLS cert"
sh /usr/local/bin/render-ctmpls.sh -k "${CONFIG_DIR}/${TLS_FULL_CHAIN_DIR}.ctmpl"

echo "Rendering TLS key file"
sh /usr/local/bin/render-ctmpls.sh -k "${CONFIG_DIR}/${TLS_PRIVATE_KEY_DIR}.ctmpl"

echo "Creating TLS secret in Kubernetes"
kubectl create secret tls \
                "${TLS_SECRET_NAME}" \
                --cert="${TLS_FULL_CHAIN_DIR}" \
                --key="${TLS_PRIVATE_KEY_DIR}" \
                --namespace="${KUBERNETES_NAMESPACE}"

echo "Generating ingress file"
sh /usr/local/bin/render-ctmpls.sh -k "${CONFIG_DIR}/lira-ingress.yaml.ctmpl"

echo "Deploying Lira Ingress"
kubectl apply -f ${CONFIG_DIR}/lira-ingress.yaml \
              --record \
              --namespace="${KUBERNETES_NAMESPACE}"




# Generate and apply the lira deployment
echo "Rendering lira config file"
sh /usr/local/bin/render-ctmpls.sh -k "${CONFIG_DIR}/${LIRA_CONFIG_FILE}.ctmpl"

echo "Deploying lira config file"
if [ ${USE_CAAS} == "true" ];
then
    kubectl create secret generic "${LIRA_CONFIG_SECRET_NAME}" \
            --from-file=config="${CONFIG_DIR}/${LIRA_CONFIG_FILE}" \
            --from-file=caas_key="${CONFIG_DIR}/${CAAS_KEY_FILE}" \
            --namespace "${KUBERNETES_NAMESPACE}"
else
    kubectl create secret generic ${LIRA_CONFIG_SECRET_NAME} \
            --from-file=config="${CONFIG_DIR}/${LIRA_CONFIG_FILE}" \
            --namespace "${KUBERNETES_NAMESPACE}"
fi

echo "Generating Lira deployment file"
sh /usr/local/bin/render-ctmpls.sh -k "${CONFIG_DIR}/${LIRA_DEPLOYMENT_YAML}.ctmpl"

echo "Deploying Lira"
kubectl apply -f ${CONFIG_DIR}/lira-deployment.yaml \
              --record \
              --namespace "${KUBERNETES_NAMESPACE}"

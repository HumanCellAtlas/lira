#!/usr/bin/env bash

# Manual Variables
LIRA_ENVIRONMENT=${LIRA_ENVIRONMENT:-"dev"}
CAAS_ENVIRONMENT=${CAAS_ENVIRONMENT:-"caas-prod"}

# Derived Variables
SERVICE=${SERVICE:-"lira"}
SVC_ACCOUNT_KEY="${CAAS_ENVIRONMENT}-key.json"
SVC_ACCOUNT_VAULT_KEY_PATH="secret/dsde/mint/${LIRA_ENVIRONMENT}/${SERVICE}/${SVC_ACCOUNT_KEY}"
VAULT_TOKEN_PATH=${VAULT_TOKEN_PATH:-"${HOME}/.vault-token"}

# Retrieve the service account key from vault
docker run -it --rm -v "${VAULT_TOKEN_PATH}":/root/.vault-token \
                    -v "${PWD}":/keys broadinstitute/dsde-toolbox:ra_rendering \
                    vault read --format=json "${SVC_ACCOUNT_VAULT_KEY_PATH}" | jq .data -r > "${SVC_ACCOUNT_KEY}"

python3 get_bearer_token.py -j "${SVC_ACCOUNT_KEY}"

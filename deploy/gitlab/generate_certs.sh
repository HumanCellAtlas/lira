#!/usr/bin/env bash

echo "Getting AWS Users credentials from Vault"
export AWS_ACCESS_KEY_ID="$(vault read -field="aws_access_key" secret/dsde/mint/${LIRA_ENVIRONMENT}/lira/aws_cert_user)"
export AWS_SECRET_ACCESS_KEY="$(vault read -field="aws_secret_key" secret/dsde/mint/${LIRA_ENVIRONMENT}/lira/aws_cert_user)"

export CERT_VAULT_DIR="/working/certs/letsencrypt/archive/${DOMAIN}/cert1.pem"
export FULLCHAIN_VAULT_DIR="/working/certs/letsencrypt/archive/${DOMAIN}/fullchain1.pem"
export PRIVKEY_VAULT_DIR="/working/certs/letsencrypt/archive/${DOMAIN}/privkey1.pem"
export CHAIN_VAULT_DIR="/working/certs/letsencrypt/archive/${DOMAIN}/chain1.pem"

echo "Making the temp directory for certs"
mktemp -d "certs"

echo "Running script"
sh "${DEPLOY_DIR}/scripts/certbot-route53.sh --agree-tos \
                             --manual-public-ip-logging-ok \
                             --email mintteam@broadinstitute.org \
                             --domains ${DOMAIN}"

export VAULT_TOKEN="$(cat ${VAULT_WRITE_TOKEN_PATH})"

echo "Writing fullchain to vault at ${FULLCHAIN_VAULT_DIR}"
vault write secret/dsde/mint/${LIRA_ENVIRONMENT}/lira/fullchain.pem value=@"${FULLCHAIN_VAULT_DIR}"

echo "Writing privkey to vault at ${PRIVKEY_VAULT_DIR}"
vault write secret/dsde/mint/${LIRA_ENVIRONMENT}/lira/privkey.pem value=@"${PRIVKEY_VAULT_DIR}"

echo "Writing chain to vault at ${CHAIN_VAULT_DIR}"
vault write secret/dsde/mint/${LIRA_ENVIRONMENT}/lira/chain.pem value=@"${CHAIN_VAULT_DIR}"

echo "Writing cert to vault at ${CERT_VAULT_DIR}"
vault write secret/dsde/mint/${LIRA_ENVIRONMENT}/lira/cert.pem value=@"${CERT_VAULT_DIR}"

export VAULT_TOKEN="$(cat ${VAULT_READ_TOKEN_PATH})"

echo "Removing local copies of certs"
rm -rf certs

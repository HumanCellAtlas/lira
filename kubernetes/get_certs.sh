#!/usr/bin/env bash

LIRA_ENVIRONMENT=${LIRA_ENVIRONMENT:-"dev"} # other valid envs: test, staging, prod

if [ ${LIRA_ENVIRONMENT} == "test" ];
then
    ENV="integration"
else
    ENV="${LIRA_ENVIRONMENT}"
fi

SERVICE=${SERVICE:-"lira"}
DOMAIN="pipelines.${ENV}.data.humancellatlas.org"
VAULT_TOKEN_PATH=${VAULT_TOKEN_PATH:-"${HOME}/.vault-token"}

echo "Getting AWS Users credentials from Vault"

AWS_ACCESS_KEY_ID="$(docker run -i \
                                --rm \
                                -v "${VAULT_TOKEN_PATH}":/root/.vault-token \
                                -v "${PWD}":/working \
                                broadinstitute/dsde-toolbox:ra_rendering \
                                vault read -field="aws_access_key" secret/dsde/mint/${LIRA_ENVIRONMENT}/${SERVICE}/aws_cert_user)"

AWS_SECRET_ACCESS_KEY="$(docker run -i \
                                    --rm \
                                    -v "${VAULT_TOKEN_PATH}":/root/.vault-token \
                                    -v "${PWD}":/working \
                                    broadinstitute/dsde-toolbox:ra_rendering \
                                    vault read -field="aws_secret_key" secret/dsde/mint/${LIRA_ENVIRONMENT}/${SERVICE}/aws_cert_user)"

echo "Making the temp directory for certs"

mktemp -d "certs"

echo "Running docker"

docker run \
    -e AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID} \
    -e AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY} \
    -v ${PWD}/certs:/working \
    humancellatlas/secondary-analysis:0.0.1 \
    bash -c \
    "cd /working && \
     cp /certs/certbot-route53/certbot-route53.sh . && \
     bash certbot-route53.sh --agree-tos \
                             --manual-public-ip-logging-ok \
                             --email mintteam@broadinstitute.org \
                             --domains ${DOMAIN}"


CERT_VAULT_DIR="/working/certs/letsencrypt/archive/${DOMAIN}/cert1.pem"
FULLCHAIN_VAULT_DIR="/working/certs/letsencrypt/archive/${DOMAIN}/fullchain1.pem"
PRIVKEY_VAULT_DIR="/working/certs/letsencrypt/archive/${DOMAIN}/privkey1.pem"
CHAIN_VAULT_DIR="/working/certs/letsencrypt/archive/${DOMAIN}/chain1.pem"

echo "Writing fullchain to vault at ${FULLCHAIN_VAULT_DIR}"

docker run -i \
           --rm \
           -v "${VAULT_TOKEN_PATH}":/root/.vault-token \
           -v "${PWD}":/working \
           broadinstitute/dsde-toolbox:ra_rendering \
           vault write secret/dsde/mint/${LIRA_ENVIRONMENT}/${SERVICE}/fullchain.pem value=@"${FULLCHAIN_VAULT_DIR}"

echo "Writing privkey to vault at ${PRIVKEY_VAULT_DIR}"

docker run -i \
           --rm \
           -v "${VAULT_TOKEN_PATH}":/root/.vault-token \
           -v "${PWD}":/working \
           broadinstitute/dsde-toolbox:ra_rendering \
           vault write secret/dsde/mint/${LIRA_ENVIRONMENT}/${SERVICE}/privkey.pem value=@"${PRIVKEY_VAULT_DIR}"

echo "Writing chain to vault at ${CHAIN_VAULT_DIR}"

docker run -i \
           --rm \
           -v "${VAULT_TOKEN_PATH}":/root/.vault-token \
           -v "${PWD}":/working \
           broadinstitute/dsde-toolbox:ra_rendering \
           vault write secret/dsde/mint/${LIRA_ENVIRONMENT}/${SERVICE}/chain.pem value=@"${CHAIN_VAULT_DIR}"

echo "Writing cert to vault at ${CERT_VAULT_DIR}"

docker run -i \
           --rm \
           -v "${VAULT_TOKEN_PATH}":/root/.vault-token \
           -v "${PWD}":/working \
           broadinstitute/dsde-toolbox:ra_rendering \
           vault write secret/dsde/mint/${LIRA_ENVIRONMENT}/${SERVICE}/cert.pem value=@"${CERT_VAULT_DIR}"

rm -rf certs

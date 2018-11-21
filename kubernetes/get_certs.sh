#!/usr/bin/env bash

LIRA_ENVIRONMENT=${LIRA_ENVIRONMENT:-""} # other valid envs: test, staging, prod

if [ ${LIRA_ENVIRONMENT} == "test" ];
then
    ENV="integration"
else
    ENV="${LIRA_ENVIRONMENT}"
fi

if [ "${ENV}" == "prod" ];
then
    DOMAIN="pipelines.data.humancellatlas.org"
else
    DOMAIN="pipelines.${ENV}.data.humancellatlas.org"
fi

VAULT_TOKEN_PATH=${VAULT_TOKEN_PATH:-"/etc/vault-token-dsde"}

echo "Getting AWS Users credentials from Vault"

AWS_ACCESS_KEY_ID="$(docker run -i \
                                --rm \
                                -v "${VAULT_TOKEN_PATH}":/root/.vault-token \
                                -v "${PWD}":/working \
                                broadinstitute/dsde-toolbox:ra_rendering \
                                vault read -field="aws_access_key" secret/dsde/mint/${LIRA_ENVIRONMENT}/lira/aws_cert_user)"

AWS_SECRET_ACCESS_KEY="$(docker run -i \
                                    --rm \
                                    -v "${VAULT_TOKEN_PATH}":/root/.vault-token \
                                    -v "${PWD}":/working \
                                    broadinstitute/dsde-toolbox:ra_rendering \
                                    vault read -field="aws_secret_key" secret/dsde/mint/${LIRA_ENVIRONMENT}/lira/aws_cert_user)"

echo "Making the temp directory for certs"

mkdir "certs"

echo "Running docker"

docker build -t certbot .

docker run \
    -e AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID} \
    -e AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY} \
    -v "$(pwd)/certbot-route53.sh":/certs/certbot-route53.sh \
    certbot:latest \
    bash -c \
        "bash /certs/certbot-route53.sh --agree-tos \
                                 --manual-public-ip-logging-ok \
                                 --email mintteam@broadinstitute.org \
                                 --domains ${DOMAIN}"


CERT_VAULT_DIR="/certs/letsencrypt/archive/${DOMAIN}/cert1.pem"
FULLCHAIN_VAULT_DIR="/certs/letsencrypt/archive/${DOMAIN}/fullchain1.pem"
PRIVKEY_VAULT_DIR="/certs/letsencrypt/archive/${DOMAIN}/privkey1.pem"
CHAIN_VAULT_DIR="/certs/letsencrypt/archive/${DOMAIN}/chain1.pem"

echo "Writing fullchain to vault at ${FULLCHAIN_VAULT_DIR}"

docker run -i \
           --rm \
           -v "${VAULT_TOKEN_PATH}":/root/.vault-token \
           -v "${PWD}":/working \
           broadinstitute/dsde-toolbox:ra_rendering \
           vault write secret/dsde/mint/${LIRA_ENVIRONMENT}/lira/fullchain.pem value=@"${FULLCHAIN_VAULT_DIR}"

echo "Writing privkey to vault at ${PRIVKEY_VAULT_DIR}"

docker run -i \
           --rm \
           -v "${VAULT_TOKEN_PATH}":/root/.vault-token \
           -v "${PWD}":/working \
           broadinstitute/dsde-toolbox:ra_rendering \
           vault write secret/dsde/mint/${LIRA_ENVIRONMENT}/lira/privkey.pem value=@"${PRIVKEY_VAULT_DIR}"

echo "Writing chain to vault at ${CHAIN_VAULT_DIR}"

docker run -i \
           --rm \
           -v "${VAULT_TOKEN_PATH}":/root/.vault-token \
           -v "${PWD}":/working \
           broadinstitute/dsde-toolbox:ra_rendering \
           vault write secret/dsde/mint/${LIRA_ENVIRONMENT}/lira/chain.pem value=@"${CHAIN_VAULT_DIR}"

echo "Writing cert to vault at ${CERT_VAULT_DIR}"

docker run -i \
           --rm \
           -v "${VAULT_TOKEN_PATH}":/root/.vault-token \
           -v "${PWD}":/working \
           broadinstitute/dsde-toolbox:ra_rendering \
           vault write secret/dsde/mint/${LIRA_ENVIRONMENT}/lira/cert.pem value=@"${CERT_VAULT_DIR}"

rm -rf certs

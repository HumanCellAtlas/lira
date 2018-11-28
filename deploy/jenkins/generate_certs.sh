#!/usr/bin/env bash

echo "Getting AWS Users credentials from Vault"
AWS_ACCESS_KEY_ID="$(docker run -i \
                                --rm \
                                -v "${VAULT_READ_TOKEN_PATH}":/root/.vault-token \
                                -v "${PWD}":/working \
                                broadinstitute/dsde-toolbox:ra_rendering \
                                vault read -field="aws_access_key" secret/dsde/mint/${LIRA_ENVIRONMENT}/lira/aws_cert_user)"
AWS_SECRET_ACCESS_KEY="$(docker run -i \
                                    --rm \
                                    -v "${VAULT_READ_TOKEN_PATH}":/root/.vault-token \
                                    -v "${PWD}":/working \
                                    broadinstitute/dsde-toolbox:ra_rendering \
                                    vault read -field="aws_secret_key" secret/dsde/mint/${LIRA_ENVIRONMENT}/lira/aws_cert_user)"

echo "Making the temp directory for certs"
mkdir "certs"

echo "Building the Certbot docker image"
docker build -t certbot .

echo "Executing the certbot script to create a cert"
docker run \
    -e AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID} \
    -e AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY} \
    -v $(pwd)/certs:/certs \
    -v ${SCRIPTS_DIR}/certbot-route53.sh:/certs/certbot-route53.sh \
    -w="/certs" \
    --privileged \
    certbot:latest \
    bash -c \
        "cat /certs/certbot-route53.sh && \
        echo \"THIS IS A TEST - A SUCCESSFUL TEST\""
#        "sudo bash /certs/certbot-route53.sh \
#                --agree-tos \
#                --manual-public-ip-logging-ok \
#                --email mintteam@broadinstitute.org \
#                --domains ${DOMAIN}"

exit 0

CERT_VAULT_DIR="certs/letsencrypt/archive/${DOMAIN}/cert1.pem"
FULLCHAIN_VAULT_DIR="certs/letsencrypt/archive/${DOMAIN}/fullchain1.pem"
PRIVKEY_VAULT_DIR="certs/letsencrypt/archive/${DOMAIN}/privkey1.pem"
CHAIN_VAULT_DIR="certs/letsencrypt/archive/${DOMAIN}/chain1.pem"

sudo chown -R jenkins certs

echo "Writing fullchain to vault at ${FULLCHAIN_VAULT_DIR}"
docker run -i \
           --rm \
           -v "${VAULT_WRITE_TOKEN_PATH}":/root/.vault-token \
           -v "${PWD}":/working \
           broadinstitute/dsde-toolbox:ra_rendering \
           vault write secret/dsde/mint/${LIRA_ENVIRONMENT}/lira/fullchain.pem value=@"${FULLCHAIN_VAULT_DIR}"

echo "Writing privkey to vault at ${PRIVKEY_VAULT_DIR}"
docker run -i \
           --rm \
           -v "${VAULT_WRITE_TOKEN_PATH}":/root/.vault-token \
           -v "${PWD}":/working \
           broadinstitute/dsde-toolbox:ra_rendering \
           vault write secret/dsde/mint/${LIRA_ENVIRONMENT}/lira/privkey.pem value=@"${PRIVKEY_VAULT_DIR}"

echo "Writing chain to vault at ${CHAIN_VAULT_DIR}"
docker run -i \
           --rm \
           -v "${VAULT_WRITE_TOKEN_PATH}":/root/.vault-token \
           -v "${PWD}":/working \
           broadinstitute/dsde-toolbox:ra_rendering \
           vault write secret/dsde/mint/${LIRA_ENVIRONMENT}/lira/chain.pem value=@"${CHAIN_VAULT_DIR}"

echo "Writing cert to vault at ${CERT_VAULT_DIR}"
docker run -i \
           --rm \
           -v "${VAULT_WRITE_TOKEN_PATH}":/root/.vault-token \
           -v "${PWD}":/working \
           broadinstitute/dsde-toolbox:ra_rendering \
           vault write secret/dsde/mint/${LIRA_ENVIRONMENT}/lira/cert.pem value=@"${CERT_VAULT_DIR}"

echo "Removing local copies of certs"
rm -rf certs

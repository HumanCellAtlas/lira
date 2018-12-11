#!/usr/bin/env bash

echo "Getting AWS Users credentials from Vault"
AWS_ACCESS_KEY_ID="$(docker run -i \
                                --rm \
                                -v "${VAULT_READ_TOKEN_PATH}":/root/.vault-token \
                                -v "${PWD}":/working \
                                broadinstitute/dsde-toolbox:ra_rendering \
                                vault read -field='aws_access_key' secret/dsde/mint/${LIRA_ENVIRONMENT}/lira/aws_cert_user)"
AWS_SECRET_ACCESS_KEY="$(docker run -i \
                                    --rm \
                                    -v "${VAULT_READ_TOKEN_PATH}":/root/.vault-token \
                                    -v "${PWD}":/working \
                                    broadinstitute/dsde-toolbox:ra_rendering \
                                    vault read -field='aws_secret_key' secret/dsde/mint/${LIRA_ENVIRONMENT}/lira/aws_cert_user)"

echo "Making the temp directory for certs"
mkdir certs

echo "Building the Certbot docker image"
cd "${DEPLOY_DIR}"
docker build -t certbot .
cd ../..

cd certs

echo "Executing the certbot script to create a cert"
docker run \
    -e AWS_ACCESS_KEY_ID="${AWS_ACCESS_KEY_ID}" \
    -e AWS_SECRET_ACCESS_KEY="${AWS_SECRET_ACCESS_KEY}" \
    -e DOMAIN="${DOMAIN}" \
    -v $(pwd):/certs \
    -v "${SCRIPTS_DIR}/certbot-route53.sh":/certs/certbot-route53.sh \
    -w /certs \
    --privileged \
    certbot:latest \
    bash -c \
        "bash /certs/certbot-route53.sh"

cd ..

sudo chown -R jenkins certs

if [ -f "certs/letsencrypt/archive/${DOMAIN}/fullchain1.pem" ];
then
    FULLCHAIN_VAULT_DIR="certs/letsencrypt/archive/${DOMAIN}/fullchain1.pem"
    echo "Writing fullchain to vault at ${FULLCHAIN_VAULT_DIR}"
    docker run -i \
               --rm \
               -v "${VAULT_WRITE_TOKEN_PATH}":/root/.vault-token \
               -v "${PWD}":/working \
               broadinstitute/dsde-toolbox:ra_rendering \
               vault write "secret/dsde/mint/${LIRA_ENVIRONMENT}/lira/fullchain.pem" value=@"${FULLCHAIN_VAULT_DIR}"
else
    echo "Fullchain file doesn't exist. Skipping..."
fi

if [ -f "certs/letsencrypt/archive/${DOMAIN}/privkey1.pem" ];
then
    PRIVKEY_VAULT_DIR="certs/letsencrypt/archive/${DOMAIN}/privkey1.pem"
    echo "Writing privkey to vault at ${PRIVKEY_VAULT_DIR}"
    docker run -i \
               --rm \
               -v "${VAULT_WRITE_TOKEN_PATH}":/root/.vault-token \
               -v "${PWD}":/working \
               broadinstitute/dsde-toolbox:ra_rendering \
               vault write "secret/dsde/mint/${LIRA_ENVIRONMENT}/lira/privkey.pem" value=@"${PRIVKEY_VAULT_DIR}"
else
    echo "Private key file doesn't exist. Skipping..."
fi

if [ -f "certs/letsencrypt/archive/${DOMAIN}/chain1.pem" ];
then
    CHAIN_VAULT_DIR="certs/letsencrypt/archive/${DOMAIN}/chain1.pem"
    echo "Writing chain to vault at ${CHAIN_VAULT_DIR}"
    docker run -i \
               --rm \
               -v "${VAULT_WRITE_TOKEN_PATH}":/root/.vault-token \
               -v "${PWD}":/working \
               broadinstitute/dsde-toolbox:ra_rendering \
               vault write "secret/dsde/mint/${LIRA_ENVIRONMENT}/lira/chain.pem" value=@"${CHAIN_VAULT_DIR}"
else
    echo "Chain file doesn't exist. Skipping..."
fi

if [ -f "certs/letsencrypt/archive/${DOMAIN}/cert1.pem" ];
then
    CERT_VAULT_DIR="certs/letsencrypt/archive/${DOMAIN}/cert1.pem"
    echo "Writing cert to vault at ${CERT_VAULT_DIR}"
    docker run -i \
               --rm \
               -v "${VAULT_WRITE_TOKEN_PATH}":/root/.vault-token \
               -v "${PWD}":/working \
               broadinstitute/dsde-toolbox:ra_rendering \
               vault write "secret/dsde/mint/${LIRA_ENVIRONMENT}/lira/cert.pem" value=@"${CERT_VAULT_DIR}"
else
    echo "Cert file doesn't exist. Skipping..."
fi

echo "Removing local copies of certs"
rm -rf certs

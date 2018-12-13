#!/usr/bin/env bash

echo "Getting AWS Users credentials from Vault"
export AWS_ACCESS_KEY_ID="$(vault read -field="aws_access_key" secret/dsde/mint/${LIRA_ENVIRONMENT}/lira/aws_cert_user)"
export AWS_SECRET_ACCESS_KEY="$(vault read -field="aws_secret_key" secret/dsde/mint/${LIRA_ENVIRONMENT}/lira/aws_cert_user)"

echo "Making the temp directory for certs"
mkdir certs

cd certs

echo "Writing certbot domain to file"
echo ${DOMAIN} > certbot_domain.txt

cat << EOF > aws_config.json
{"access_key": "${AWS_ACCESS_KEY_ID}", "secret_key": "${AWS_SECRET_ACCESS_KEY}"}
EOF

echo "Running certbot-route53 script"
sh "${SCRIPTS_DIR}"/certbot-route53.sh

cd ..

export VAULT_TOKEN="$(cat ${VAULT_WRITE_TOKEN_PATH})"

if [ -f "${WORK_DIR}/certs/letsencrypt/archive/${DOMAIN}/fullchain1.pem" ];
then
    export FULLCHAIN_VAULT_DIR="${WORK_DIR}/certs/letsencrypt/archive/${DOMAIN}/fullchain1.pem"
    echo "Writing fullchain to vault at ${FULLCHAIN_VAULT_DIR}"
    vault write secret/dsde/mint/${LIRA_ENVIRONMENT}/lira/fullchain.pem value=@"${FULLCHAIN_VAULT_DIR}"
else
    echo "Fullchain file doesn't exist. Skipping..."
fi

if [ -f "${WORK_DIR}/certs/letsencrypt/archive/${DOMAIN}/privkey1.pem" ];
then
    export PRIVKEY_VAULT_DIR="${WORK_DIR}/certs/letsencrypt/archive/${DOMAIN}/privkey1.pem"
    echo "Writing privkey to vault at ${PRIVKEY_VAULT_DIR}"
    vault write secret/dsde/mint/${LIRA_ENVIRONMENT}/lira/privkey.pem value=@"${PRIVKEY_VAULT_DIR}"
else
    echo "Private key file doesn't exist. Skipping..."
fi

if [ -f "${WORK_DIR}/certs/letsencrypt/archive/${DOMAIN}/chain1.pem" ];
then
    export CHAIN_VAULT_DIR="${WORK_DIR}/certs/letsencrypt/archive/${DOMAIN}/chain1.pem"
    echo "Writing chain to vault at ${CHAIN_VAULT_DIR}"
    vault write secret/dsde/mint/${LIRA_ENVIRONMENT}/lira/chain.pem value=@"${CHAIN_VAULT_DIR}"
else
    echo "Chain file doesn't exist. Skipping..."
fi

if [ -f "${WORK_DIR}/certs/letsencrypt/archive/${DOMAIN}/cert1.pem" ];
then
    export CERT_VAULT_DIR="${WORK_DIR}/certs/letsencrypt/archive/${DOMAIN}/cert1.pem"
    echo "Writing cert to vault at ${CERT_VAULT_DIR}"
    vault write secret/dsde/mint/${LIRA_ENVIRONMENT}/lira/cert.pem value=@"${CERT_VAULT_DIR}"
else
    echo "Cert file doesn't exist. Skipping..."
fi

export VAULT_TOKEN="$(cat ${VAULT_READ_TOKEN_PATH})"

echo "Removing local copies of certs"
rm -rf certs

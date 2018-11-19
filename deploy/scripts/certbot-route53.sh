#!/usr/bin/env bash

# This script was taken from this repo: https://github.com/jed/certbot-route53.git
# It was copied locally is built on the fly because no docker image exists with this code
# I copied the file locally because it is self contained and there is no reason to grab the whole repo
# every time that we want to do a deployment of a new cert

set -ex

MYSELF="$(cd "$(dirname "$0")" && pwd)/$(basename "$0")"

# Check that certbot domain exists. If not, then create letsencrypt directory and make the cert challenge
if [ -z "${CERTBOT_DOMAIN}" ]; then

    mkdir -p "${PWD}/letsencrypt"

    certbot certonly \
        --non-interactive \
        --manual \
        --manual-auth-hook "${MYSELF}" \
        --preferred-challenge dns \
        --config-dir "${PWD}/letsencrypt" \
        --work-dir "${PWD}/letsencrypt" \
        --logs-dir "${PWD}/letsencrypt" \
        --agree-tos \
        --manual-public-ip-logging-ok \
        --email mintteam@broadinstitute.org \
        --domains "${DOMAIN}"

else
    echo "Reading CERTBOT_DOMAIN from file"
    CERTBOT_DOMAIN=$(cat certbot_domain.txt)
    echo "CERTBOT_DOMAIN=${CERTBOT_DOMAIN}"

    [[ ${CERTBOT_AUTH_OUTPUT} ]] && ACTION="DELETE" || ACTION="UPSERT"

    printf -v QUERY 'HostedZones[?Name == `%s.`]|[?Config.PrivateZone == `false`].Id' "${CERTBOT_DOMAIN}"

    HOSTED_ZONE_ID="$(aws route53 list-hosted-zones --query "${QUERY}" --output text)"

    if [ -z "${HOSTED_ZONE_ID:?}" ]; then
        # CERTBOT_DOMAIN is a hostname, not a domain (zone)
        # We strip out the hostname part to leave only the domain
#        DOMAIN="$(sed -r 's/^[^.]+.(.*)$/\1/' <<< "${CERTBOT_DOMAIN:?}")"
        DOMAIN="$(echo "${CERTBOT_DOMAIN:?}" | sed -r 's/^[^.]+.(.*)$/\1/')"

        printf -v QUERY 'HostedZones[?Name == `%s.`]|[?Config.PrivateZone == `false`].Id' "${DOMAIN}"

        HOSTED_ZONE_ID="$(aws route53 list-hosted-zones --query "${QUERY}" --output text)"
    fi

    if [ -z "${HOSTED_ZONE_ID}" ]; then
        if [ -n "${DOMAIN}" ]; then
          echo "No hosted zone found that matches domain ${DOMAIN} or hostname ${CERTBOT_DOMAIN}"
        else
          echo "No hosted zone found that matches ${CERTBOT_DOMAIN}"
        fi
        exit 1
    fi

    aws route53 wait resource-record-sets-changed --id "$(
        aws route53 change-resource-record-sets \
            --hosted-zone-id "${HOSTED_ZONE_ID}" \
            --query ChangeInfo.Id --output text \
            --change-batch "{
                \"Changes\": [{
                    \"Action\": \"${ACTION}\",
                        \"ResourceRecordSet\": {
                            \"Name\": \"_acme-challenge.${CERTBOT_DOMAIN}.\",
                            \"ResourceRecords\": [{\"Value\": \"\\\"${CERTBOT_VALIDATION}\\\"\"}],
                            \"Type\": \"TXT\",
                            \"TTL\": 30
                        }
                    }]
                }"
    )"

fi
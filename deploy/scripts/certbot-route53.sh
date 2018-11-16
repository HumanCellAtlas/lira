#!/usr/bin/env bash

# This script was taken from this repo: https://github.com/jed/certbot-route53.git
# It was copied locally is built on the fly because no docker image exists with this code
# I copied the file locally because it is self contained and there is no reason to grab the whole repo
# every time that we want to do a deployment of a new cert

set -ex

MYSELF="$(cd "$(dirname "$0")" && pwd)/$(basename "$0")"

echo "******************************************************************************"
echo "AFTER MYSELF DEFINITION"
echo "MYSELF: ${MYSELF}"
echo "CERTBOT_DOMAIN: ${CERTBOT_DOMAIN}"
echo "CERTBOT_AUTH_OUTPUT: ${CERTBOT_AUTH_OUTPUT}"
echo "ACTION: ${ACTION}"
echo "******************************************************************************"


if [ -z "${CERTBOT_DOMAIN}" ]; then
  mkdir -p "${PWD}/letsencrypt"

  certbot certonly \
    --non-interactive \
    --manual \
    --manual-auth-hook "${MYSELF}" \
    --manual-cleanup-hook "${MYSELF}" \
    --preferred-challenge dns \
    --config-dir "${PWD}/letsencrypt" \
    --work-dir "${PWD}/letsencrypt" \
    --logs-dir "${PWD}/letsencrypt" \
    "$@"

else
  [[ ${CERTBOT_AUTH_OUTPUT} ]] && ACTION="DELETE" || ACTION="UPSERT"

  printf -v QUERY 'HostedZones[?Name == `%s.`]|[?Config.PrivateZone == `false`].Id' "${CERTBOT_DOMAIN}"

echo "******************************************************************************"
echo "AFTER FIRST QUERY DEFINITION"
echo "MYSELF: ${MYSELF}"
echo "CERTBOT_DOMAIN: ${CERTBOT_DOMAIN}"
echo "CERTBOT_AUTH_OUTPUT: ${CERTBOT_AUTH_OUTPUT}"
echo "ACTION: ${ACTION}"
echo "QUERY: ${QUERY}"
echo "******************************************************************************"

  HOSTED_ZONE_ID="$(aws route53 list-hosted-zones --query "${QUERY}" --output text)"

echo "******************************************************************************"
echo "AFTER HOSTED ZONE ID DEFINITION"
echo "MYSELF: ${MYSELF}"
echo "CERTBOT_DOMAIN: ${CERTBOT_DOMAIN}"
echo "CERTBOT_AUTH_OUTPUT: ${CERTBOT_AUTH_OUTPUT}"
echo "ACTION: ${ACTION}"
echo "******************************************************************************"

  if [ -z "${HOSTED_ZONE_ID}" ]; then
    # CERTBOT_DOMAIN is a hostname, not a domain (zone)
    # We strip out the hostname part to leave only the domain
    DOMAIN="$(sed -r 's/^[^.]+.(.*)$/\1/' <<< "${CERTBOT_DOMAIN}")"

    printf -v QUERY 'HostedZones[?Name == `%s.`]|[?Config.PrivateZone == `false`].Id' "${DOMAIN}"

echo "******************************************************************************"
echo "AFTER SECOND QUERY DEFINITION"
echo "MYSELF: ${MYSELF}"
echo "CERTBOT_DOMAIN: ${CERTBOT_DOMAIN}"
echo "CERTBOT_AUTH_OUTPUT: ${CERTBOT_AUTH_OUTPUT}"
echo "ACTION: ${ACTION}"
echo "QUERY: ${QUERY}"
echo "******************************************************************************"

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

echo "******************************************************************************"
echo "RIGHT BEFORE CALL TO AWS"
echo "MYSELF: ${MYSELF}"
echo "CERTBOT_DOMAIN: ${CERTBOT_DOMAIN}"
echo "CERTBOT_AUTH_OUTPUT: ${CERTBOT_AUTH_OUTPUT}"
echo "ACTION: ${ACTION}"
echo "QUERY: ${QUERY}"
echo "******************************************************************************"

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

  echo 1
fi
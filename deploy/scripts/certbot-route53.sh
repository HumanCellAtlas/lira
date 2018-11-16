#!/usr/bin/env bash

set -ex

# This script was taken from this repo: https://github.com/jed/certbot-route53.git
# It was copied locally is built on the fly because no docker image exists with this code
# I copied the file locally because it is self contained and there is no reason to grab the whole repo
# every time that we want to do a deployment of a new cert


MYSELF="$(cd "$(dirname "$0")" && pwd)/$(basename "$0")"
echo "************************************ CERTBOT_DOMAIN 1: ${DOMAIN} *************************************"

# If the domain variable is null or empty, then create the letsencrypt directory and run certbot.
if [ -z "${DOMAIN}" ]; then
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

  printf -v QUERY 'HostedZones[?Name == `%s.`]|[?Config.PrivateZone == `false`].Id' "${DOMAIN}"

  HOSTED_ZONE_ID="$(aws route53 list-hosted-zones --query "${QUERY}" --output text)"

  if [ -z "${HOSTED_ZONE_ID}" ]; then
    # DOMAIN is a hostname, not a domain (zone)
    # We strip out the hostname part to leave only the domain

#    PROCESSED_DOMAIN="$(sed -r 's/^[^.]+.(.*)$/\1/' <<< "${DOMAIN}")"

    printf -v QUERY 'HostedZones[?Name == `%s.`]|[?Config.PrivateZone == `false`].Id' "${DOMAIN}"

    echo "******************************************************************************************"
    echo "******************************************************************************************"
    echo "QUERY: ${QUERY}"
    echo "******************************************************************************************"
    echo "******************************************************************************************"

    HOSTED_ZONE_ID="$(aws route53 list-hosted-zones --query "${QUERY}" --output text)"
  fi

  if [ -z "${HOSTED_ZONE_ID}" ]; then
#    if [ -n "${PROCESSED_DOMAIN}" ]; then
#      echo "No hosted zone found that matches domain ${PROCESSED_DOMAIN} or hostname ${DOMAIN}"
#    else
      echo "No hosted zone found that matches ${DOMAIN}"
#    fi
    exit 1
  fi

echo "******************************************************************************************"
echo "******************************************************************************************"
echo "aws route53 wait resource-record-sets-changed --id $\("
echo "  aws route53 change-resource-record-sets \\"
echo "      --hosted-zone-id ${HOSTED_ZONE_ID} \\"
echo "      --query ChangeInfo.Id \\"
echo "      --output text \\"
echo "      --change-batch {"
echo "          \"Changes\": [{"
echo "              \"Action\": \"${ACTION}\","
echo "              \"ResourceRecordSet\": {"
echo "              \"Name\": \"_acme-challenge.${DOMAIN}.\","
echo "              \"ResourceRecords\": [{\"Value\": \"\\\"${CERTBOT_VALIDATION}\\\"\"}],"
echo "              \"Type\": \"TXT\","
echo "              \"TTL\": 30"
echo "              }"
echo "          }]"
echo "      }"
echo ")"
echo "******************************************************************************************"
echo "******************************************************************************************"

  aws route53 wait resource-record-sets-changed --id "$(
    aws route53 change-resource-record-sets \
    --hosted-zone-id "${HOSTED_ZONE_ID}" \
    --query ChangeInfo.Id \
    --output text \
    --change-batch "{
      \"Changes\": [{
        \"Action\": \"${ACTION}\",
        \"ResourceRecordSet\": {
          \"Name\": \"_acme-challenge.${DOMAIN}.\",
          \"ResourceRecords\": [{\"Value\": \"\\\"${CERTBOT_VALIDATION}\\\"\"}],
          \"Type\": \"TXT\",
          \"TTL\": 30
        }
      }]
    }"
  )"

  echo 1
fi

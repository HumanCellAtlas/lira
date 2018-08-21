#!/usr/bin/env bash

#uuid=$1
#source config.sh

ENV=dev
DSS_URL=${DSS_URL:-"https://dss.${ENV}.data.humancellatlas.org/v1/subscriptions"}
BLUEBOX_KEY_PATH="/Users/ranthony/GitHub/HumanCellAtlas/lira/kubernetes/bluebox-subscription-manager-dev-key.json"
UUID="c01dcbf0-b721-4982-87ab-4a8651d189eb"

python3 subscription-delete.py "${DSS_URL}/${UUID}?replica=gcp" ${BLUEBOX_KEY_PATH}

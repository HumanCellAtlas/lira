#!/usr/bin/env bash

ENV=dev
DSS_URL=${DSS_URL:-"https://dss.${ENV}.data.humancellatlas.org/v1/subscriptions"}
BLUEBOX_KEY_PATH="/Users/ranthony/GitHub/HumanCellAtlas/lira/kubernetes/bluebox-subscription-manager-dev-key.json"

python3 subscriptions-list.py "${DSS_URL}?replica=gcp" ${BLUEBOX_KEY_PATH}

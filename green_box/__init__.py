#!/usr/bin/env python

"""
Green box description FIXME: elaborate
"""
import os
import json
import logging
import connexion
from connexion.resolver import RestyResolver
from listener_utils import ListenerConfig
from listener_utils import GoogleCloudStorageClient

logging.basicConfig(level=logging.DEBUG)

# TODO: Move code from __init__ into __main__ and shorten the call chain.
# Create lazy initialized GCS client here
gcs_client = GoogleCloudStorageClient(key_location='/etc/secondary-analysis/bucket-reader-key.json',
                                      scopes=['https://www.googleapis.com/auth/devstorage.read_only'])
app = connexion.App(__name__)

config_path = os.environ['listener_config']
with open(config_path) as f:
    app.app.config = ListenerConfig(json.load(f), app.app.config)
    app.app.gcs_client = gcs_client

resolver = RestyResolver("green_box.api", collection_endpoint_name="list")
app.add_api('../green_box.yml', resolver=resolver, validate_responses=True)

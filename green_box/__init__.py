#!/usr/bin/env python

"""
Green box description FIXME: elaborate
"""
import os
import json
import logging
import connexion
from connexion.resolver import RestyResolver
from .config import ListenerConfig

logging.basicConfig(level=logging.DEBUG)
from listener_utils import LazyProperty, GoogleCloudStorageClient

# Create lazy initialized GCS client here
client = GoogleCloudStorageClient(key_location='/etc/secondary-analysis/bucket-reader-key.json',
                                  scopes=['https://www.googleapis.com/auth/devstorage.read_only'])
app = connexion.App(__name__)

config_path = os.environ['listener_config']
with open(config_path) as f:
    app.app.config = ListenerConfig(json.load(f), app.app.config)
    app.app.client = client

resolver = RestyResolver("green_box.api", collection_endpoint_name="list")
app.add_api('../green_box.yml', resolver=resolver, validate_responses=True)

#!/usr/bin/env python3

import os
import json
import logging
import connexion
from connexion.resolver import RestyResolver
from google.cloud import storage
from google.auth.exceptions import DefaultCredentialsError
from google.oauth2 import service_account
from .config import ListenerConfig
logging.basicConfig(level=logging.DEBUG)

"""
Green box description FIXME: elaborate
"""

# Important global google cloud storage authentication process 
try:
    key_location='/etc/secondary-analysis/bucket-reader-key.json'
    scopes=['https://www.googleapis.com/auth/devstorage.read_only']
    credentials = service_account.Credentials.from_service_account_file(
        key_location, scopes=scopes)
    storage_client = storage.Client(credentials=credentials, project=credentials.project_id)
    logging.debug('Configuring listener credentials using %s' % key_location)

except IOError:
    logging.debug(
        'Could not configure listener using expected json key or default credentials')


# Prepare for the app
app = connexion.App(__name__)


config_path = os.environ['listener_config']
with open(config_path) as f:
    app.app.config = ListenerConfig(json.load(f), app.app.config)

# Store storage_client
app.app.client = storage_client

# resolver = RestyResolver("green_box.api", collection_endpoint_name="list")
resolver = RestyResolver("api", collection_endpoint_name="list")


app.add_api('../green_box.yml', resolver=resolver, validate_responses=True)


if __name__ == '__main__':
    app.run(debug=True, port=8080)
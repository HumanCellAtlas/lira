#!/usr/bin/env python

"""
Green box description FIXME: elaborate
"""
import os
import json
import logging
import connexion
from connexion.resolver import RestyResolver

import config
from pipeline_tools import gcs_utils


def main():
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger("Lira | {module_path}".format(module_path=__name__))

    # Create lazy initialized GCS client here
    gcs_client = gcs_utils.GoogleCloudStorageClient(key_location='/etc/secondary-analysis/bucket-reader-key.json',
                                          scopes=['https://www.googleapis.com/auth/devstorage.read_only'])
    app = connexion.App(__name__)

    config_path = os.environ['listener_config']
    with open(config_path) as f:
        app.app.config = config.ListenerConfig(json.load(f), app.app.config)
        app.app.gcs_client = gcs_client

    resolver = RestyResolver("api", collection_endpoint_name="list")
    app.add_api('lira.yml', resolver=resolver, validate_responses=True)
    app.run(port=8080)

    logger.info("Lira started to run")

if __name__ == '__main__':
    main()

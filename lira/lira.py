#!/usr/bin/env python

"""
Human Cell Atlas Data Coordination Platform Data Processing Pipeline Service (“Secondary-Analysis”) Notification
listener API.

In the HCA DCP, data processing refers to the use of a computational pipeline to analyze raw experimental data
from a specific assay. Processing of HCA data produces collections of quality metrics and features that can be
used for further analysis. The Data Processing Pipeline Service consists of analysis pipelines and execution
infrastructure.

This listener API Lira listens for notifications and start workflows.
"""
import os
import json
import logging
import connexion
from connexion.resolver import RestyResolver
from swagger_ui_bundle import swagger_ui_3_path
import argparse
from datetime import datetime

from . import lira_utils
from . import lira_config


parser = argparse.ArgumentParser()
parser.add_argument('--host', default='0.0.0.0')
parser.add_argument('--port', type=int, default=8080)
args, _ = parser.parse_known_args()


# Define the Connexion App with Swagger UI v3
options = {'swagger_path': swagger_ui_3_path}
app = connexion.FlaskApp(__name__, options=options)


# Load the config file
config_path = os.environ['lira_config']
with open(config_path) as f:
    config = lira_config.LiraConfig(json.load(f), app.app.config)


# Configure the logger
logger = logging.getLogger(f'lira.{__name__}')
logger.info(f"Using config file at {config_path}")


# Note down the launch time
app.app.launch_time = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')


# Consume the config and initialize the LRU cache for WDL submissions
app.app.config = config
app.app.prepare_submission = lira_utils.create_prepare_submission_function(
    app.app.config.cache_wdls
)


# Use automatic routing with custom resolver: https://github.com/zalando/connexion#automatic-routing
resolver = RestyResolver('lira.api', collection_endpoint_name='list')
arguments = {'API_DOMAIN_NAME': config.DOMAIN}
app.add_api(
    'lira_api.yml', resolver=resolver, validate_responses=True, arguments=arguments
)


if __name__ == '__main__':
    app.run(host=args.host, port=args.port)

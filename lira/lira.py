#!/usr/bin/env python

"""
Green box description FIXME: elaborate
"""
import os
import json
import logging
import connexion
from connexion.resolver import RestyResolver
import argparse

from . import lira_config
from .api import notifications

parser = argparse.ArgumentParser()
parser.add_argument('--host', default='0.0.0.0')
parser.add_argument('--port', type=int, default=8080)
args, _ = parser.parse_known_args()

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('Lira | {module_path}'.format(module_path=__name__))

app = connexion.App(__name__)

# 'application' is not used in this file, but is used by gunicorn
application = app.app

config_path = os.environ['listener_config']
logger.info('Using config file at {0}'.format(config_path))
with open(config_path) as f:
    config = lira_config.LiraConfig(json.load(f), app.app.config)
    app.app.config = config

    # Configure log level for loggers that print query params.
    # Unless specified otherwise in Lira's config file, these will be set
    # at ERROR for werkzeug and INFO for connexion.decorators.validation
    # in order to suppress messages that include query params.
    logging.getLogger('werkzeug').setLevel(config.log_level_werkzeug)
    logging.getLogger('connexion.decorators.validation').setLevel(config.log_level_connexion_validation)

    app.app.prepare_submission = notifications.create_prepare_submission_function(app.app.config.cache_wdls)

resolver = RestyResolver('lira.api', collection_endpoint_name='list')
app.add_api('lira.yml', resolver=resolver, validate_responses=True)

if __name__ == '__main__':
    app.run(host=args.host, port=args.port)

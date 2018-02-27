#!/usr/bin/env python

"""
Green box description FIXME: elaborate
"""
import os
import sys
import json
import logging
import connexion
from connexion.resolver import RestyResolver
import argparse

from . import lira_config
from .api import notifications

class MaxLevelFilter(object):
    """Excludes logs above max_level"""
    def __init__(self, max_level):
        self.max_level = max_level
    def filter(self, log_record):
        return log_record.levelno <= self.max_level

parser = argparse.ArgumentParser()
parser.add_argument('--host', default='0.0.0.0')
parser.add_argument('--port', type=int, default=8080)
args, _ = parser.parse_known_args()

app = connexion.App(__name__)

# 'application' is not used in this file, but is used by gunicorn
application = app.app

config_path = os.environ['listener_config']
with open(config_path) as f:
    config = lira_config.LiraConfig(json.load(f), app.app.config)

logger = logging.getLogger('lira.{module_path}'.format(module_path=__name__))
logger.info('Using config file at {0}'.format(config_path))
app.app.config = config
app.app.prepare_submission = notifications.create_prepare_submission_function(app.app.config.cache_wdls)

resolver = RestyResolver('lira.api', collection_endpoint_name='list')
app.add_api('lira.yml', resolver=resolver, validate_responses=True)

if __name__ == '__main__':
    app.run(host=args.host, port=args.port)

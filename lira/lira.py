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
import arrow

from . import lira_utils
from . import lira_config


parser = argparse.ArgumentParser()
parser.add_argument('--host', default='0.0.0.0')
parser.add_argument('--port', type=int, default=8080)
args, _ = parser.parse_known_args()

app = connexion.App(__name__)

config_path = os.environ['listener_config']
with open(config_path) as f:
    config = lira_config.LiraConfig(json.load(f), app.app.config)

logger = logging.getLogger('lira.{module_path}'.format(module_path=__name__))
logger.info('Using config file at {0}'.format(config_path))

app.app.launch_time = arrow.utcnow().format('YYYY-MM-DD HH:mm:ss ZZ')
app.app.config = config
app.app.prepare_submission = lira_utils.create_prepare_submission_function(app.app.config.cache_wdls)

resolver = RestyResolver('lira.api', collection_endpoint_name='list')
app.add_api('lira.yml', resolver=resolver, validate_responses=True)

if __name__ == '__main__':
    app.run(host=args.host, port=args.port)
